"""Sanitization and data loss prevention stripping credentials, tokens, and PII from pipeline text.

Note: Redaction is best-effort, not a formal security guarantee.
"""

import re
from collections.abc import Callable

from ichnoscope.models import Culprit, Incident

# Compiled pattern specifications. Quantifiers are bounded to prevent catastrophic backtracking.
PATTERNS: list[tuple[str, re.Pattern[str], str | Callable[[re.Match[str]], str]]] = [
    # Private Key blocks across lines
    (
        "private_key",
        re.compile(r"-----BEGIN [A-Z0-9 _-]+PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 _-]+PRIVATE KEY-----"),
        "[REDACTED:private_key]",
    ),
    # Slack Webhooks
    (
        "slack_webhook",
        re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9_-]{3,64}/[A-Za-z0-9_-]{3,64}/[A-Za-z0-9_-]{10,64}"),
        "[REDACTED:slack_webhook]",
    ),
    # URL credentials (keep scheme, user, and host; redact only password)
    (
        "url_credentials",
        re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^:\s/@]+):(?!\[REDACTED:)([^@\s/]+)(@[^/\s]+)"),
        r"\1:[REDACTED:url_credentials]\3",
    ),
    # GitHub Tokens
    (
        "github_token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b|\bgithub_pat_[A-Za-z0-9_]{22,255}\b"),
        "[REDACTED:github_token]",
    ),
    # AWS Access Keys
    (
        "aws_key",
        re.compile(r"\b(A[KS]IA)[0-9A-Z]{16}\b"),
        "[REDACTED:aws_key]",
    ),
    # Google API Keys
    (
        "google_key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        "[REDACTED:google_key]",
    ),
    # Slack Tokens
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,255}\b"),
        "[REDACTED:slack_token]",
    ),
    # Stripe API Keys
    (
        "stripe_key",
        re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{16,255}\b"),
        "[REDACTED:stripe_key]",
    ),
    # LLM API Keys (OpenAI, Anthropic, etc.)
    (
        "llm_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,255}\b"),
        "[REDACTED:llm_key]",
    ),
    # JWT Tokens
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED:jwt]",
    ),
    # Bearer / Basic Authentication Headers (keep Bearer/Basic keyword)
    (
        "bearer",
        re.compile(r"\b(Bearer|Basic)\s+(?!\[REDACTED:)([A-Za-z0-9_.-]{16,255})\b"),
        r"\1 [REDACTED:bearer]",
    ),
    # Quoted Secret Literals (key must contain secret/token/password/etc., value 8+ chars)
    (
        "secret_literal",
        re.compile(
            r"""(?i)(["']?(?:[a-zA-Z0-9_]*(?:password|passwd|secret|token|api_key|apikey|access_key|client_secret)[a-zA-Z0-9_]*)["']?\s*[:=]\s*)(["'])(?!\[REDACTED:)([^"'\r\n]{8,})\2"""
        ),
        r"\1\2[REDACTED:secret_literal]\2",
    ),
    # Secret Environment Variable Assignments (ALL-CAPS key=unquoted_value 8+ chars)
    (
        "secret_env",
        re.compile(
            r"""\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|API_KEY|ACCESS_KEY)[A-Z0-9_]*\s*=\s*)(?!\[REDACTED:)([^\s(\[{\'"][^\s(\[{]{7,})"""
        ),
        r"\1[REDACTED:secret_env]",
    ),
    # Email Addresses
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED:email]",
    ),
]


def redact_with_report(text: str) -> tuple[str, dict[str, int]]:
    """Sanitize secrets and PII from text, returning the redacted text and counts by kind."""
    if not isinstance(text, str):
        raise TypeError(f"redact expects a string, got {type(text).__name__}")

    if not text:
        return "", {}

    counts: dict[str, int] = {}
    result = text

    for kind, pattern, replacement in PATTERNS:
        matches = len(pattern.findall(result))
        if matches > 0:
            counts[kind] = counts.get(kind, 0) + matches
            result = pattern.sub(replacement, result)

    return result, counts


def redact(text: str) -> str:
    """Sanitize secrets and PII from text using best-effort heuristic matching."""
    redacted_text, _ = redact_with_report(text)
    return redacted_text


def redact_incident(incident: Incident) -> Incident:
    """Return a new Incident copy with error_message and stack_excerpt sanitized."""
    return incident.model_copy(
        update={
            "error_message": redact(incident.error_message),
            "stack_excerpt": redact(incident.stack_excerpt),
        }
    )


def redact_culprit(culprit: Culprit) -> Culprit:
    """Return a new Culprit copy with message and diff sanitized."""
    return culprit.model_copy(
        update={
            "message": redact(culprit.message),
            "diff": redact(culprit.diff),
        }
    )
