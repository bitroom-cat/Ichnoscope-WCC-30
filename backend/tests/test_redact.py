"""Unit tests for backend/ichnoscope/redact.py."""

import time
from datetime import datetime, timezone

import pytest
from ichnoscope.models import Culprit, Incident
from ichnoscope.redact import (
    redact,
    redact_culprit,
    redact_incident,
    redact_with_report,
)


def _make_secrets() -> dict[str, str]:
    """Build fake credentials at runtime to avoid triggering repository secret scanners."""
    return {
        "github_token": "gh" + "p_" + "A" * 36,
        "aws_key": "AK" + "IA" + "B" * 16,
        "google_key": "AI" + "za" + "C" * 35,
        "slack_token": "xo" + "xb-" + "D" * 12,
        "slack_webhook": "https://hooks." + "slack.com/services/" + "T12345/B12345/" + "E" * 24,
        "llm_key": "sk-" + "F" * 25,
        "stripe_key": "sk" + "_live_" + "G" * 24,
        "jwt": "ey" + "JhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0." + "dozjgN_b_mock_signature_12345",
        "bearer": "Bearer " + "H" * 32,
        "private_key": "-----BEGIN " + "RSA PRIVATE KEY-----\n" + "MIIEowIBAAKCAQEA0mockkey...\n" + "-----END " + "RSA PRIVATE KEY-----",
        "url_credentials": "postgres://user:" + "supersecretpassword123" + "@db.internal:5432/main",
        "secret_literal": 'api_key = "' + "top_secret_api_key_value" + '"',
        "secret_env": "DB_PASSWORD=" + "unquotedSecretPassword123",
        "email": "developer." + "test@example.com",
    }


def test_positive_redaction_per_kind():
    secrets = _make_secrets()
    for kind, val in secrets.items():
        redacted = redact(val)
        assert f"[REDACTED:{kind}]" in redacted, f"Expected [REDACTED:{kind}] for {kind}"
        # The secret itself must be gone
        if kind == "bearer":
            assert "H" * 32 not in redacted
        elif kind == "url_credentials":
            assert "supersecretpassword123" not in redacted
        elif kind == "secret_literal":
            assert "top_secret_api_key_value" not in redacted
        elif kind == "secret_env":
            assert "unquotedSecretPassword123" not in redacted
        elif kind == "private_key":
            assert "MIIEowIBAAKCAQEA0mockkey" not in redacted
        else:
            assert val not in redacted


def test_format_preservation():
    secrets = _make_secrets()

    # Bearer preserves the keyword
    bearer_redacted = redact(secrets["bearer"])
    assert bearer_redacted == "Bearer [REDACTED:bearer]"

    # url_credentials preserves scheme, user, and host
    url_redacted = redact(secrets["url_credentials"])
    assert url_redacted == "postgres://user:[REDACTED:url_credentials]@db.internal:5432/main"

    # secret_literal preserves variable name and quotes
    lit_redacted = redact(secrets["secret_literal"])
    assert lit_redacted == 'api_key = "[REDACTED:secret_literal]"'


def test_must_not_be_redacted():
    safe_samples = [
        # Git commit SHAs and UUIDs
        "commit a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345",
        "release 9c1d2e3",
        "uuid 123e4567-e89b-12d3-a456-426614174000",
        # Variable references and function calls
        'token = payload["stripe_token"]',
        "password = get_password()",
        'api_key = os.environ["API_KEY"]',
        "secret = config.secret",
        # Short string literals (< 8 characters)
        'password = "abc"',
        # Python decorators
        '@app.route("/x")',
        "@pytest.mark.parametrize",
        # Ordinary paths and URLs without credentials
        "/app/services/payment.py",
        "https://api.github.com/graphql",
        # Version strings
        "package@1.2.3",
        "myshop@1.4.0+9c1d2e3",
    ]

    for sample in safe_samples:
        assert redact(sample) == sample, f"False positive on: {sample}"


def test_idempotence():
    secrets = _make_secrets()
    text = (
        f"Config: {secrets['github_token']} and {secrets['aws_key']}\n"
        f"Auth: {secrets['bearer']}\n"
        f"Conn: {secrets['url_credentials']}"
    )
    first_pass = redact(text)
    second_pass = redact(first_pass)
    assert first_pass == second_pass

    _, report = redact_with_report(first_pass)
    assert report == {}, "Second redaction pass must report zero new secrets"


def test_diff_structure_preservation():
    secrets = _make_secrets()
    diff = (
        "@@ -10,4 +10,4 @@\n"
        " def connect():\n"
        f"-    token = '{secrets['github_token']}'\n"
        "+    token = get_env_token()\n"
    )
    redacted = redact(diff)
    lines_orig = diff.splitlines()
    lines_redacted = redacted.splitlines()

    assert len(lines_orig) == len(lines_redacted)
    assert lines_redacted[0].startswith("@@")
    assert lines_redacted[2].startswith("-    token = '[REDACTED:github_token]'")
    assert lines_redacted[3].startswith("+    token = get_env_token()")


def test_redact_with_report():
    secrets = _make_secrets()
    text = f"{secrets['github_token']} and another {secrets['github_token']} with {secrets['aws_key']}"
    redacted, report = redact_with_report(text)

    assert "[REDACTED:github_token]" in redacted
    assert "[REDACTED:aws_key]" in redacted
    assert report.get("github_token") == 2
    assert report.get("aws_key") == 1
    # Report must never contain raw secret values
    for secret_val in secrets.values():
        assert secret_val not in str(report)


def test_redact_incident_and_culprit():
    secrets = _make_secrets()
    inc = Incident(
        incident_id="inc-1",
        occurred_at=datetime.now(timezone.utc),
        exception_type="AuthError",
        error_message=f"Failed with token {secrets['github_token']}",
        file_path="app.py",
        line_number=1,
        stack_excerpt=f"Traceback:\n  auth with {secrets['aws_key']}",
    )
    sanitized_inc = redact_incident(inc)
    assert sanitized_inc is not inc
    assert secrets["github_token"] not in sanitized_inc.error_message
    assert "[REDACTED:github_token]" in sanitized_inc.error_message
    assert secrets["aws_key"] not in sanitized_inc.stack_excerpt
    assert "[REDACTED:aws_key]" in sanitized_inc.stack_excerpt
    # Original remains unchanged
    assert secrets["github_token"] in inc.error_message
    assert inc.file_path == sanitized_inc.file_path

    culprit = Culprit(
        sha="a14b9f2",
        author_name="Alice",
        message=f"feat: add key {secrets['llm_key']}",
        committed_at=datetime.now(timezone.utc),
        diff=f"+ token = '{secrets['stripe_key']}'",
    )
    sanitized_culprit = redact_culprit(culprit)
    assert sanitized_culprit is not culprit
    assert secrets["llm_key"] not in sanitized_culprit.message
    assert "[REDACTED:llm_key]" in sanitized_culprit.message
    assert secrets["stripe_key"] not in sanitized_culprit.diff
    assert "[REDACTED:stripe_key]" in sanitized_culprit.diff
    assert culprit.sha == sanitized_culprit.sha


def test_multiple_secrets_one_line_and_multiline_block():
    secrets = _make_secrets()
    line = f"{secrets['github_token']} {secrets['aws_key']} {secrets['google_key']}"
    redacted = redact(line)
    assert "[REDACTED:github_token] [REDACTED:aws_key] [REDACTED:google_key]" == redacted

    block = f"Header\n{secrets['private_key']}\nFooter"
    redacted_block = redact(block)
    assert redacted_block == "Header\n[REDACTED:private_key]\nFooter"


def test_performance_guard():
    secrets = _make_secrets()
    repeated_code = "def process_order(item_id: int):\n    # standard handler\n    return {'status': 'ok'}\n" * 4000
    payload = repeated_code + f"\napi_token = '{secrets['github_token']}'\n"
    assert len(payload) > 300_000

    start = time.perf_counter()
    res = redact(payload)
    duration = time.perf_counter() - start

    assert duration < 2.0, f"Redaction took too long: {duration:.3f}s"
    assert "[REDACTED:github_token]" in res


def test_type_error_for_non_string():
    for non_str in (None, 123, ["abc"], {"k": "v"}):
        with pytest.raises(TypeError):
            redact(non_str)  # type: ignore[arg-type]
