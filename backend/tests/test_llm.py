"""Unit tests for backend/ichnoscope/llm.py."""

import json
from unittest.mock import MagicMock

import httpx
import pytest
from ichnoscope.config import load_settings
from ichnoscope.llm import LLMError, complete_structured
from ichnoscope.models import Explanation
from pydantic import BaseModel, Field


class Demo(BaseModel):
    answer: str
    items: list[str] = Field(default_factory=list)


def _make_chat_response(content: str | dict | None) -> dict:
    if isinstance(content, dict):
        text = json.dumps(content)
    elif content is None:
        text = None
    else:
        text = content
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1728000000,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }


def test_success_on_first_provider():
    recorded_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(
            200,
            json=_make_chat_response({"answer": "hello", "items": ["a", "b"]}),
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq",
        "GROQ_API_KEY": "test-key-groq",
        "GROQ_MODEL": "llama-3.3-70b-versatile",
    })

    result = complete_structured(
        Demo,
        system="system prompt",
        user="user query",
        settings=settings,
        client=client,
    )

    assert result.value.answer == "hello"
    assert result.value.items == ["a", "b"]
    assert result.provider == "groq"
    assert result.model == "llama-3.3-70b-versatile"
    assert len(result.attempts) == 1
    assert result.attempts[0].outcome == "ok"
    assert result.attempts[0].http_status == 200

    # Captured request checks
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.url.path == "/openai/v1/chat/completions"
    assert req.headers["Authorization"] == "Bearer test-key-groq"
    assert req.headers["Content-Type"] == "application/json"

    body = json.loads(req.content.decode("utf-8"))
    assert body["model"] == "llama-3.3-70b-versatile"
    assert body["temperature"] == 0.1
    assert body["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user query"},
    ]
    assert body["response_format"] == {"type": "json_object"}


def test_chain_order():
    called_hosts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        called_hosts.append(request.url.host)
        # Groq fails, then Gemini succeeds
        if "groq.com" in request.url.host:
            return httpx.Response(500, json={"error": "server error"})
        return httpx.Response(
            200,
            json=_make_chat_response({"answer": "from-gemini", "items": []}),
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq,gemini",
        "GROQ_API_KEY": "key-groq",
        "GROQ_MODEL": "llama-groq",
        "GEMINI_API_KEY": "key-gemini",
        "GEMINI_MODEL": "gemini-flash",
    })

    result = complete_structured(Demo, "sys", "usr", settings=settings, client=client)
    assert called_hosts[0] == "api.groq.com"
    assert "generativelanguage.googleapis.com" in called_hosts[1]
    assert result.provider == "gemini"
    assert len(result.attempts) == 2
    assert result.attempts[0].outcome == "server_error"
    assert result.attempts[1].outcome == "ok"


@pytest.mark.parametrize(
    ("fail_action", "expected_outcome", "expected_status"),
    [
        (429, "rate_limited", 429),
        (500, "server_error", 500),
        ("timeout", "timeout", None),
        ("network", "network_error", None),
        (401, "auth_error", 401),
        (403, "auth_error", 403),
        (404, "not_found", 404),
        (418, "bad_request", 418),
    ],
)
def test_fallback_on_failure_types(fail_action, expected_outcome, expected_status):
    def handler(request: httpx.Request) -> httpx.Response:
        if "groq.com" in request.url.host:
            if fail_action == "timeout":
                raise httpx.ReadTimeout("read timed out")
            if fail_action == "network":
                raise httpx.ConnectError("connection refused")
            return httpx.Response(int(fail_action), text="fail")
        return httpx.Response(200, json=_make_chat_response({"answer": "ok-gemini", "items": []}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq,gemini",
        "GROQ_API_KEY": "k1",
        "GROQ_MODEL": "m1",
        "GEMINI_API_KEY": "k2",
        "GEMINI_MODEL": "m2",
    })

    res = complete_structured(Demo, "sys", "usr", settings=settings, client=client)
    assert res.provider == "gemini"
    assert res.attempts[0].outcome == expected_outcome
    assert res.attempts[0].http_status == expected_status
    assert res.attempts[1].outcome == "ok"


@pytest.mark.parametrize(
    "bad_response_json",
    [
        {"choices": []},
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": ""}}]},
        {"choices": [{"message": {"content": 42}}]},
        {"id": "no-choices"},
    ],
)
def test_empty_responses(bad_response_json):
    def handler(request: httpx.Request) -> httpx.Response:
        if "groq.com" in request.url.host:
            return httpx.Response(200, json=bad_response_json)
        return httpx.Response(200, json=_make_chat_response({"answer": "ok-gemini", "items": []}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq,gemini",
        "GROQ_API_KEY": "k1",
        "GROQ_MODEL": "m1",
        "GEMINI_API_KEY": "k2",
        "GEMINI_MODEL": "m2",
    })

    res = complete_structured(Demo, "sys", "usr", settings=settings, client=client)
    assert res.provider == "gemini"
    assert res.attempts[0].outcome == "empty_response"
    assert res.attempts[1].outcome == "ok"


def test_json_extraction():
    # 1. Wrapped in ```json code fence
    def h1(r: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_chat_response('```json\n{"answer": "fenced", "items": []}\n```'))

    c1 = httpx.Client(transport=httpx.MockTransport(h1))
    s1 = load_settings({"LLM_CHAIN": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"})
    res1 = complete_structured(Demo, "sys", "usr", settings=s1, client=c1)
    assert res1.value.answer == "fenced"

    # 2. Prose before and after
    def h2(r: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_make_chat_response('Here is the requested output:\n{"answer": "embedded", "items": []}\nHope that helps!'),
        )

    c2 = httpx.Client(transport=httpx.MockTransport(h2))
    res2 = complete_structured(Demo, "sys", "usr", settings=s1, client=c2)
    assert res2.value.answer == "embedded"

    # 3. Top-level list is invalid_json
    def h3(r: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_chat_response('[{"answer": "list"}]'))

    c3 = httpx.Client(transport=httpx.MockTransport(h3))
    with pytest.raises(LLMError) as exc_info:
        complete_structured(Demo, "sys", "usr", settings=s1, client=c3)
    assert exc_info.value.attempts[0].outcome == "invalid_json"

    # 4. Plain prose is invalid_json
    def h4(r: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_chat_response("I cannot fulfill this request."))

    c4 = httpx.Client(transport=httpx.MockTransport(h4))
    with pytest.raises(LLMError) as exc_info:
        complete_structured(Demo, "sys", "usr", settings=s1, client=c4)
    assert exc_info.value.attempts[0].outcome == "invalid_json"

    # 5. Truncated JSON is invalid_json
    def h5(r: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_chat_response('{"answer": "incomp'))

    c5 = httpx.Client(transport=httpx.MockTransport(h5))
    with pytest.raises(LLMError) as exc_info:
        complete_structured(Demo, "sys", "usr", settings=s1, client=c5)
    assert exc_info.value.attempts[0].outcome == "invalid_json"


def test_schema_validation_and_normalize():
    # Model requiring exactly 3 checklist items
    class StrictModel(BaseModel):
        domain: str
        items: list[str] = Field(min_length=3, max_length=3)

    # Provider 1 returns invalid checklist length -> schema_invalid, fallback to provider 2
    def handler(request: httpx.Request) -> httpx.Response:
        if "groq.com" in request.url.host:
            return httpx.Response(
                200,
                json=_make_chat_response({"domain": "Backend", "items": ["1", "2"]}),
            )
        # Provider 2 returns with an extra reasoning key
        return httpx.Response(
            200,
            json=_make_chat_response({
                "domain": "Backend",
                "items": ["1", "2", "3"],
                "reasoning": "thought process",
            }),
        )

    def normalize_hook(data: dict) -> dict:
        d = dict(data)
        if "domain" in d:
            d["domain"] = d["domain"].lower()
        return d

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq,gemini",
        "GROQ_API_KEY": "k1",
        "GROQ_MODEL": "m1",
        "GEMINI_API_KEY": "k2",
        "GEMINI_MODEL": "m2",
    })

    res = complete_structured(
        StrictModel,
        "sys",
        "usr",
        settings=settings,
        client=client,
        normalize=normalize_hook,
    )
    assert res.provider == "gemini"
    assert res.value.domain == "backend"
    assert len(res.value.items) == 3
    assert not hasattr(res.value, "reasoning")
    assert res.attempts[0].outcome == "schema_invalid"
    assert res.attempts[1].outcome == "ok"


def test_json_mode_retry():
    calls_groq: list[bool] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        has_rf = "response_format" in body
        calls_groq.append(has_rf)

        if has_rf:
            return httpx.Response(
                400,
                text="Invalid parameter: response_format is not supported for this model",
            )
        return httpx.Response(200, json=_make_chat_response({"answer": "recovered", "items": []}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({"LLM_CHAIN": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"})

    res = complete_structured(Demo, "sys", "usr", settings=settings, client=client)
    assert calls_groq == [True, False]
    assert len(res.attempts) == 2
    assert res.attempts[0].outcome == "bad_request"
    assert "retrying without response_format" in res.attempts[0].detail
    assert res.attempts[1].outcome == "ok"
    assert res.value.answer == "recovered"


def test_all_providers_fail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq,gemini",
        "GROQ_API_KEY": "test-key-groq-secret",
        "GROQ_MODEL": "m1",
        "GEMINI_API_KEY": "test-key-gemini-secret",
        "GEMINI_MODEL": "m2",
    })

    with pytest.raises(LLMError) as exc_info:
        complete_structured(Demo, "system sensitive data", "user sensitive code", settings=settings, client=client)

    err = exc_info.value
    assert len(err.attempts) == 2
    assert err.attempts[0].provider == "groq"
    assert err.attempts[1].provider == "gemini"

    err_str = str(err)
    assert "groq=server_error" in err_str
    assert "gemini=server_error" in err_str
    # Must NOT reveal secrets or prompt/response text
    assert "test-key-groq-secret" not in err_str
    assert "test-key-gemini-secret" not in err_str
    assert "system sensitive data" not in err_str
    assert "user sensitive code" not in err_str


def test_no_providers_configured():
    settings = load_settings({})
    spy_handler = MagicMock()
    client = httpx.Client(transport=httpx.MockTransport(spy_handler))

    with pytest.raises(LLMError) as exc_info:
        complete_structured(Demo, "sys", "usr", settings=settings, client=client)

    assert exc_info.value.attempts == []
    assert not spy_handler.called


def test_total_budget():
    simulated_time = 0.0

    def fake_clock() -> float:
        return simulated_time

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal simulated_time
        simulated_time += 30.0  # Each call consumes 30s
        return httpx.Response(500, text="fail")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "groq,gemini,openrouter",
        "GROQ_API_KEY": "k1",
        "GROQ_MODEL": "m1",
        "GEMINI_API_KEY": "k2",
        "GEMINI_MODEL": "m2",
        "OPENROUTER_API_KEY": "k3",
        "OPENROUTER_MODEL": "m3",
    })

    with pytest.raises(LLMError) as exc_info:
        complete_structured(
            Demo,
            "sys",
            "usr",
            settings=settings,
            client=client,
            total_budget_s=50.0,
            clock=fake_clock,
        )

    attempts = exc_info.value.attempts
    assert len(attempts) == 3
    assert attempts[0].outcome == "server_error"  # at t=0, advances to t=30
    assert attempts[1].outcome == "server_error"  # at t=30, advances to t=60
    assert attempts[2].outcome == "skipped_budget"  # at t=60, >= 50 budget, skipped without calling


def test_redaction_before_network():
    captured_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(200, json=_make_chat_response({"answer": "ok", "items": []}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({"LLM_CHAIN": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"})

    fake_token = "gh" + "p_" + "K" * 36
    user_msg = f"Stack with token: {fake_token}"

    complete_structured(Demo, "sys", user_msg, settings=settings, client=client)

    assert len(captured_payloads) == 1
    sent_user = captured_payloads[0]["messages"][1]["content"]
    assert fake_token not in sent_user
    assert "[REDACTED:github_token]" in sent_user


def test_no_key_provider_has_no_auth_header():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json=_make_chat_response({"answer": "ok", "items": []}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "ollama",
        "OLLAMA_MODEL": "llama3",
    })

    complete_structured(Demo, "sys", "usr", settings=settings, client=client)

    assert len(captured_requests) == 1
    assert "Authorization" not in captured_requests[0].headers


def test_url_building():
    captured_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_urls.append(str(request.url))
        return httpx.Response(200, json=_make_chat_response({"answer": "ok", "items": []}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "LLM_CHAIN": "gemini",
        "GEMINI_API_KEY": "k",
        "GEMINI_MODEL": "m",
        "GEMINI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai/",
    })

    complete_structured(Demo, "sys", "usr", settings=settings, client=client)
    assert captured_urls[0] == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def test_client_lifecycle(monkeypatch):
    # 1. Passed-in client is NOT closed
    injected_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json=_make_chat_response({"answer": "ok", "items": []}))
        )
    )
    settings = load_settings({"LLM_CHAIN": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"})
    complete_structured(Demo, "sys", "usr", settings=settings, client=injected_client)
    assert not injected_client.is_closed
    injected_client.close()

    # 2. When client is None, function creates and closes its own client
    spy_close = MagicMock()
    real_init = httpx.Client.__init__

    def mock_init(self, *args, **kwargs):
        real_init(self, *args, transport=httpx.MockTransport(lambda r: httpx.Response(200, json=_make_chat_response({"answer": "ok", "items": []}))), **kwargs)
        self.close = spy_close

    monkeypatch.setattr(httpx.Client, "__init__", mock_init)
    complete_structured(Demo, "sys", "usr", settings=settings, client=None)
    assert spy_close.called


def test_safe_attempt_details():
    api_key_secret = "secret-super-sensitive-key-xyz"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text=f"rate limit with key {api_key_secret}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({"LLM_CHAIN": "groq", "GROQ_API_KEY": api_key_secret, "GROQ_MODEL": "m"})

    with pytest.raises(LLMError) as exc_info:
        complete_structured(Demo, "sys", "usr", settings=settings, client=client)

    for attempt in exc_info.value.attempts:
        assert len(attempt.detail) <= 120
        assert api_key_secret not in attempt.detail


def test_real_model_explanation():
    valid_explanation_dict = {
        "domain": "backend",
        "root_cause_hypothesis": "The stripe token was missing in charge payload.",
        "checklist": [
            "Check payload parameter stripe_token",
            "Verify webhook payload format",
            "Deploy hotfix to staging",
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_make_chat_response(valid_explanation_dict))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({"LLM_CHAIN": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"})

    res = complete_structured(Explanation, "sys", "usr", settings=settings, client=client)
    assert isinstance(res.value, Explanation)
    assert res.value.domain == "backend"
    assert res.value.root_cause_hypothesis == "The stripe token was missing in charge payload."
    assert len(res.value.checklist) == 3
