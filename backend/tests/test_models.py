"""Unit tests for backend/ichnoscope/models.py."""

from datetime import datetime, timezone

import pytest
from ichnoscope.models import (
    Culprit,
    Explanation,
    Incident,
    RunState,
    explanation_json_schema,
)
from pydantic import ValidationError


def test_incident_naive_datetime_becomes_utc():
    naive = datetime(2026, 10, 4, 12, 30, 45)  # noqa: DTZ001 - explicitly testing naive datetime handling
    inc = Incident(
        incident_id="inc-1",
        occurred_at=naive,
        exception_type="KeyError",
        error_message="missing user",
        file_path="app/main.py",
        line_number=42,
        stack_excerpt="traceback...",
    )
    assert inc.occurred_at.tzinfo is not None
    assert inc.occurred_at.tzinfo == timezone.utc
    assert inc.occurred_at.hour == 12
    assert inc.occurred_at.minute == 30


def test_incident_file_path_normalization():
    # Only leading "/" and "./" are stripped; directories remain intact
    inc1 = Incident(
        incident_id="inc-1",
        occurred_at=datetime.now(timezone.utc),
        exception_type="KeyError",
        error_message="err",
        file_path="/app/x.py",
        line_number=10,
        stack_excerpt="trace",
    )
    assert inc1.file_path == "app/x.py"

    inc2 = Incident(
        incident_id="inc-2",
        occurred_at=datetime.now(timezone.utc),
        exception_type="KeyError",
        error_message="err",
        file_path="./x.py",
        line_number=10,
        stack_excerpt="trace",
    )
    assert inc2.file_path == "x.py"

    inc3 = Incident(
        incident_id="inc-3",
        occurred_at=datetime.now(timezone.utc),
        exception_type="KeyError",
        error_message="err",
        file_path="./services/payment/handler.py",
        line_number=10,
        stack_excerpt="trace",
    )
    assert inc3.file_path == "services/payment/handler.py"


def test_incident_line_number_zero_rejected():
    with pytest.raises(ValidationError):
        Incident(
            incident_id="inc-bad",
            occurred_at=datetime.now(timezone.utc),
            exception_type="ValueError",
            error_message="err",
            file_path="app.py",
            line_number=0,
            stack_excerpt="trace",
        )


def test_incident_stack_excerpt_truncated():
    long_stack = "x" * 5000
    inc = Incident(
        incident_id="inc-long",
        occurred_at=datetime.now(timezone.utc),
        exception_type="IndexError",
        error_message="err",
        file_path="main.py",
        line_number=1,
        stack_excerpt=long_stack,
    )
    assert len(inc.stack_excerpt) == 4000
    assert inc.stack_excerpt == "x" * 4000


def test_incident_extra_fields_ignored():
    inc = Incident(
        incident_id="inc-extra",
        occurred_at=datetime.now(timezone.utc),
        exception_type="IndexError",
        error_message="err",
        file_path="main.py",
        line_number=1,
        stack_excerpt="trace",
        unknown_metadata_field="should_be_ignored",
    )
    assert not hasattr(inc, "unknown_metadata_field")


def test_culprit_diff_truncation():
    # Diff over 6000 chars is truncated and ends with marker
    long_diff = "a" * 7000
    culprit = Culprit(
        sha="a89f30b",
        author_name="Alice",
        message="feat: something",
        committed_at=datetime.now(timezone.utc),
        diff=long_diff,
    )
    assert len(culprit.diff) == 6000 + len("\n... [truncated]")
    assert culprit.diff.endswith("\n... [truncated]")
    assert culprit.diff.startswith("a" * 6000)

    # Short diff is unchanged
    short_diff = "diff --git a/foo.py b/foo.py\n+hello"
    culprit_short = Culprit(
        sha="a89f30b",
        author_name="Alice",
        message="feat: something",
        committed_at=datetime.now(timezone.utc),
        diff=short_diff,
    )
    assert culprit_short.diff == short_diff


def test_culprit_naive_datetime_becomes_utc():
    naive = datetime(2026, 10, 4, 10, 15, 0)  # noqa: DTZ001 - explicitly testing naive datetime handling
    culprit = Culprit(
        sha="a89f30b",
        author_name="Alice",
        message="fix: bug",
        committed_at=naive,
    )
    assert culprit.committed_at.tzinfo is not None
    assert culprit.committed_at.tzinfo == timezone.utc


def test_explanation_valid():
    exp = Explanation(
        domain="backend",
        root_cause_hypothesis="   Unchecked array index access raises IndexError.   ",
        checklist=[
            " Verify index boundary check in handler.py ",
            "Run unit test with empty list fixture",
            "Deploy fix to staging",
        ],
    )
    assert exp.domain == "backend"
    assert exp.root_cause_hypothesis == "Unchecked array index access raises IndexError."
    assert exp.checklist == [
        "Verify index boundary check in handler.py",
        "Run unit test with empty list fixture",
        "Deploy fix to staging",
    ]


def test_explanation_checklist_length_validation():
    # 2 items fail
    with pytest.raises(ValidationError):
        Explanation(
            domain="backend",
            root_cause_hypothesis="hypothesis",
            checklist=["Step 1", "Step 2"],
        )

    # 4 items fail
    with pytest.raises(ValidationError):
        Explanation(
            domain="backend",
            root_cause_hypothesis="hypothesis",
            checklist=["Step 1", "Step 2", "Step 3", "Step 4"],
        )


def test_explanation_checklist_empty_item_fails():
    with pytest.raises(ValidationError):
        Explanation(
            domain="backend",
            root_cause_hypothesis="hypothesis",
            checklist=["Step 1", "   ", "Step 3"],
        )


def test_explanation_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Explanation(
            domain="backend",
            root_cause_hypothesis="hypothesis",
            checklist=["Step 1", "Step 2", "Step 3"],
            hallucinated_sha="123456",
        )


def test_explanation_bad_domain_fails():
    with pytest.raises(ValidationError):
        Explanation(
            domain="mobile",  # Not in Literal["backend", "frontend", "database", "infra"]
            root_cause_hypothesis="hypothesis",
            checklist=["Step 1", "Step 2", "Step 3"],
        )


def test_runstate_isolated_logs_and_add_log():
    state1 = RunState(payload={"event_id": "1"})
    state2 = RunState(payload={"event_id": "2"})

    state1.add_log("Received Sentry event")

    assert len(state1.logs) == 1
    assert len(state2.logs) == 0
    assert "Received Sentry event" in state1.logs[0]

    # Verify log format: "HH:MM:SS message"
    time_part, message_part = state1.logs[0].split(" ", 1)
    parts = time_part.split(":")
    assert len(parts) == 3
    assert message_part == "Received Sentry event"


def test_explanation_json_schema():
    schema = explanation_json_schema()
    assert isinstance(schema, dict)
    assert "checklist" in schema.get("properties", {})
    assert "root_cause_hypothesis" in schema.get("properties", {})
    assert "domain" in schema.get("properties", {})
