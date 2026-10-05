"""Unit tests for backend/ichnoscope/severity.py."""

from datetime import datetime, timezone

import pytest
from ichnoscope.config import Settings, load_settings
from ichnoscope.models import Incident
from ichnoscope.severity import rate, rate_with_reason


def make_incident(**overrides) -> Incident:
    """Helper to create a valid Incident instance with defaults and custom overrides."""
    kwargs = {
        "incident_id": "test-inc-1",
        "occurred_at": datetime.now(timezone.utc),
        "exception_type": "ValueError",
        "error_message": "test error",
        "file_path": "services/order.py",
        "line_number": 42,
        "stack_excerpt": "stack excerpt",
        "environment": "production",
        "event_count": 1,
        "users_affected": 0,
    }
    kwargs.update(overrides)
    return Incident(**kwargs)


@pytest.mark.parametrize(
    ("users", "events", "expected_sev"),
    [
        (49, 99, "P2-High"),
        (50, 1, "P1-Critical"),
        (1, 100, "P1-Critical"),
        (10, 1, "P2-High"),
        (9, 19, "P3-Medium"),
        (0, 20, "P2-High"),
    ],
)
def test_boundaries_with_defaults(users, events, expected_sev):
    inc = make_incident(users_affected=users, event_count=events, environment="production")
    settings = load_settings({})
    sev = rate(inc, settings)
    assert sev == expected_sev
    assert sev in {"P1-Critical", "P2-High", "P3-Medium"}


@pytest.mark.parametrize("env", ["staging", "development", ""])
def test_non_production_is_always_p3(env):
    inc = make_incident(users_affected=10_000, event_count=10_000, environment=env)
    settings = load_settings({})
    sev, reason = rate_with_reason(inc, settings)
    assert sev == "P3-Medium"
    assert "not a production environment" in reason
    assert env in reason


@pytest.mark.parametrize("env", ["PRODUCTION", " prod ", "Production", "prod"])
def test_production_environment_spelling(env):
    inc = make_incident(users_affected=50, event_count=1, environment=env)
    settings = load_settings({})
    assert rate(inc, settings) == "P1-Critical"


def test_custom_thresholds():
    settings = load_settings({
        "P1_USERS": "5",
        "P1_EVENTS": "10",
        "P2_USERS": "2",
        "P2_EVENTS": "4",
    })
    inc_p1 = make_incident(users_affected=5, event_count=1)
    assert rate(inc_p1, settings) == "P1-Critical"

    inc_p2 = make_incident(users_affected=2, event_count=1)
    assert rate(inc_p2, settings) == "P2-High"

    inc_p3 = make_incident(users_affected=1, event_count=1)
    assert rate(inc_p3, settings) == "P3-Medium"


def test_zero_disables_rule():
    # P1_EVENTS=0 disables the P1 check on event_count
    settings = Settings(p1_users=50, p1_events=0, p2_users=10, p2_events=20)
    inc = make_incident(users_affected=5, event_count=10_000, environment="production")
    # 10_000 events doesn't trigger P1 since P1_EVENTS=0; falls through to P2 (event_count >= 20)
    sev, reason = rate_with_reason(inc, settings)
    assert sev == "P2-High"
    assert "events >= 20" in reason

    # Users rule still triggers P1
    inc_p1_users = make_incident(users_affected=50, event_count=10_000, environment="production")
    sev_users, _ = rate_with_reason(inc_p1_users, settings)
    assert sev_users == "P1-Critical"


def test_reason_strings():
    settings = load_settings({})

    # P1 by both: mentions users first and contains deciding numbers
    inc_both = make_incident(users_affected=63, event_count=120)
    _, reason_both = rate_with_reason(inc_both, settings)
    assert "63" in reason_both
    assert "50" in reason_both
    assert "120" in reason_both
    assert "100" in reason_both
    assert reason_both.index("users") < reason_both.index("events")

    # P2 by events: contains deciding numbers
    inc_p2_events = make_incident(users_affected=5, event_count=22)
    _, reason_p2 = rate_with_reason(inc_p2_events, settings)
    assert "22" in reason_p2
    assert "20" in reason_p2

    # P3 below thresholds
    inc_p3 = make_incident(users_affected=9, event_count=19)
    _, reason_p3 = rate_with_reason(inc_p3, settings)
    assert "below thresholds" in reason_p3
    assert "9 users" in reason_p3
    assert "19 events" in reason_p3


@pytest.mark.parametrize(
    ("users", "events", "env"),
    [
        (50, 1, "production"),
        (1, 100, "production"),
        (20, 20, "production"),
        (1, 1, "production"),
        (500, 500, "staging"),
    ],
)
def test_rate_matches_rate_with_reason(users, events, env):
    inc = make_incident(users_affected=users, event_count=events, environment=env)
    settings = load_settings({})
    sev = rate(inc, settings)
    sev_from_tuple, _ = rate_with_reason(inc, settings)
    assert sev == sev_from_tuple
    assert sev in {"P1-Critical", "P2-High", "P3-Medium"}
