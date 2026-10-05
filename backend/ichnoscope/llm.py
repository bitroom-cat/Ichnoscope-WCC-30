"""OpenAI-compatible LLM transport layer executing ordered fallback chains with validation and redaction."""

import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from ichnoscope.config import LLMProvider, Settings
from ichnoscope.redact import redact

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S: float = 20.0
DEFAULT_TOTAL_BUDGET_S: float = 60.0


@dataclass(frozen=True)
class Attempt:
    """Diagnostic outcome record of an invocation attempt against a specific LLM provider."""

    provider: str
    model: str
    outcome: str
    http_status: int | None
    elapsed_ms: int
    detail: str


@dataclass(frozen=True)
class StructuredResult(Generic[T]):
    """Successful result containing parsed Pydantic model and full attempt audit trail."""

    value: T
    provider: str
    model: str
    attempts: list[Attempt]


class LLMError(Exception):
    """Raised when all providers in the configured LLM fallback chain fail or none are available."""

    def __init__(self, message: str, attempts: list[Attempt] | None = None) -> None:
        super().__init__(message)
        self.attempts: list[Attempt] = attempts or []


def _extract_and_validate_json(
    content: str,
    model_cls: type[T],
    normalize: Callable[[dict], dict] | None,
) -> tuple[T | None, str, str]:
    """Extract first JSON object from response content, clean keys, normalize, and validate."""
    stripped = content.strip()
    # Strip markdown code blocks if wrapped
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
        stripped = stripped.strip()

    start_idx = stripped.find("{")
    if start_idx == -1:
        return None, "invalid_json", "no JSON object in content"

    # Reject if top-level structure is an array
    first_bracket = stripped.find("[")
    if first_bracket != -1 and first_bracket < start_idx:
        return None, "invalid_json", "top-level JSON is a list, not an object"

    try:
        data, _ = json.JSONDecoder().raw_decode(stripped, start_idx)
    except (json.JSONDecodeError, ValueError) as err:
        return None, "invalid_json", f"JSONDecodeError: {type(err).__name__}"[:120]

    if not isinstance(data, dict):
        return None, "invalid_json", "top-level JSON is not an object"

    # Drop top-level keys not defined on the target model
    allowed_keys = set(model_cls.model_fields.keys())
    cleaned_dict = {k: v for k, v in data.items() if k in allowed_keys}

    if normalize is not None:
        try:
            cleaned_dict = normalize(cleaned_dict)
        except Exception as err:  # noqa: BLE001 - user-supplied normalize hook may raise arbitrary exceptions
            return None, "schema_invalid", f"NormalizeError: {type(err).__name__}"[:120]

    try:
        parsed_model = model_cls.model_validate(cleaned_dict)
        return parsed_model, "ok", "ok"
    except ValidationError as val_err:
        first_loc = ".".join(str(loc) for loc in val_err.errors()[0]["loc"]) if val_err.errors() else "root"
        return None, "schema_invalid", f"ValidationError: {first_loc}"[:120]


def _post_chat(
    client: httpx.Client,
    provider: LLMProvider,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
    include_response_format: bool,
) -> httpx.Response:
    """Send an HTTP POST request to the provider's /chat/completions endpoint."""
    url = f"{provider.base_url.rstrip('/')}/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if provider.api_key is not None:
        headers["Authorization"] = f"Bearer {provider.api_key.get_secret_value()}"

    payload: dict = {
        "model": provider.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if include_response_format:
        payload["response_format"] = {"type": "json_object"}

    return client.post(url, json=payload, headers=headers, timeout=timeout_s)


def complete_structured(
    model_cls: type[T],
    system: str,
    user: str,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    normalize: Callable[[dict], dict] | None = None,
    temperature: float = 0.1,
    max_tokens: int = 800,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    total_budget_s: float = DEFAULT_TOTAL_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> StructuredResult[T]:
    """Execute LLM call across configured provider chain until a validated model is produced."""
    if settings is None:
        from ichnoscope.config import get_settings

        settings = get_settings()

    providers = settings.llm_providers()
    if not providers:
        raise LLMError("no usable LLM provider configured", attempts=[])

    # Redact user message before it leaves machine
    safe_user = redact(user)

    attempts: list[Attempt] = []
    start_time = clock()

    own_client = client is None
    http_client = httpx.Client() if own_client else client

    try:
        for provider in providers:
            now = clock()
            if (now - start_time) >= total_budget_s:
                attempts.append(
                    Attempt(
                        provider=provider.name,
                        model=provider.model,
                        outcome="skipped_budget",
                        http_status=None,
                        elapsed_ms=0,
                        detail="budget exceeded before call",
                    )
                )
                continue

            # Attempt provider invocation with json_object response_format first
            include_rf = True
            for _ in range(2):  # loop allows at most 1 JSON-mode retry on same provider
                t0 = clock()
                resp = None
                status = None
                try:
                    resp = _post_chat(
                        client=http_client,
                        provider=provider,
                        system=system,
                        user=safe_user,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout_s=timeout_s,
                        include_response_format=include_rf,
                    )
                    status = resp.status_code
                    elapsed_ms = int((clock() - t0) * 1000)
                except httpx.TimeoutException as exc:
                    elapsed_ms = int((clock() - t0) * 1000)
                    attempts.append(
                        Attempt(
                            provider=provider.name,
                            model=provider.model,
                            outcome="timeout",
                            http_status=None,
                            elapsed_ms=elapsed_ms,
                            detail=type(exc).__name__[:120],
                        )
                    )
                    break
                except httpx.TransportError as exc:
                    elapsed_ms = int((clock() - t0) * 1000)
                    attempts.append(
                        Attempt(
                            provider=provider.name,
                            model=provider.model,
                            outcome="network_error",
                            http_status=None,
                            elapsed_ms=elapsed_ms,
                            detail=type(exc).__name__[:120],
                        )
                    )
                    break

                # Check if retry without response_format is warranted
                if include_rf and status in (400, 422):
                    body_lower = resp.text.lower()
                    if any(term in body_lower for term in ("response_format", "json_object", "json mode")):
                        attempts.append(
                            Attempt(
                                provider=provider.name,
                                model=provider.model,
                                outcome="bad_request",
                                http_status=status,
                                elapsed_ms=elapsed_ms,
                                detail=f"HTTP {status} (retrying without response_format)"[:120],
                            )
                        )
                        include_rf = False
                        continue  # retry same provider once without response_format

                # Process HTTP status
                if status == 429:
                    attempts.append(Attempt(provider.name, provider.model, "rate_limited", 429, elapsed_ms, "HTTP 429"))
                    break
                if status is not None and 500 <= status < 600:
                    attempts.append(Attempt(provider.name, provider.model, "server_error", status, elapsed_ms, f"HTTP {status}"))
                    break
                if status in (401, 403):
                    attempts.append(Attempt(provider.name, provider.model, "auth_error", status, elapsed_ms, f"HTTP {status}"))
                    break
                if status == 404:
                    attempts.append(Attempt(provider.name, provider.model, "not_found", 404, elapsed_ms, "HTTP 404"))
                    break
                if status != 200:
                    attempts.append(Attempt(provider.name, provider.model, "bad_request", status, elapsed_ms, f"HTTP {status}"))
                    break

                # 200 OK: Inspect JSON structure
                try:
                    resp_json = resp.json()
                except (json.JSONDecodeError, ValueError):
                    attempts.append(
                        Attempt(provider.name, provider.model, "invalid_json", 200, elapsed_ms, "response body not JSON")
                    )
                    break

                choices = resp_json.get("choices")
                if not isinstance(choices, list) or not choices:
                    attempts.append(
                        Attempt(provider.name, provider.model, "empty_response", 200, elapsed_ms, "missing or empty choices")
                    )
                    break

                first_choice = choices[0]
                message = first_choice.get("message") if isinstance(first_choice, dict) else None
                content = message.get("content") if isinstance(message, dict) else None

                if content is None or not isinstance(content, str) or not content.strip():
                    attempts.append(
                        Attempt(provider.name, provider.model, "empty_response", 200, elapsed_ms, "content empty or not string")
                    )
                    break

                parsed_val, outcome, detail = _extract_and_validate_json(content, model_cls, normalize)
                attempts.append(Attempt(provider.name, provider.model, outcome, 200, elapsed_ms, detail))

                if outcome == "ok" and parsed_val is not None:
                    return StructuredResult(
                        value=parsed_val,
                        provider=provider.name,
                        model=provider.model,
                        attempts=attempts,
                    )

                # Validation or JSON extraction failed on this provider; move to next
                break

    finally:
        if own_client:
            http_client.close()

    summary = ", ".join(f"{a.provider}={a.outcome}" for a in attempts)
    raise LLMError(f"all {len(attempts)} providers failed: {summary}", attempts=attempts)
