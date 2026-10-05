"""Unit tests for backend/ichnoscope/parse.py."""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from ichnoscope.config import get_settings
from ichnoscope.parse import ParseError, parse_sentry

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"


def _load_fixture(filename: str) -> dict:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def test_bug1_keyerror_payment():
    payload = _load_fixture("bug1_keyerror_payment.json")
    inc = parse_sentry(payload, path_prefix_strip="/app/")

    assert inc.exception_type == "KeyError"
    assert inc.error_message == "'stripe_token'"
    assert inc.file_path == "services/payment.py"
    assert inc.line_number == 84
    assert inc.release_sha == "a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345"
    assert inc.occurred_at.tzinfo == timezone.utc
    assert inc.event_count == 120
    assert inc.users_affected == 63
    assert "services/payment.py:84 in charge_card" in inc.stack_excerpt
    assert 'token = payload["stripe_token"]' in inc.stack_excerpt


def test_bug2_attributeerror_cart():
    payload = _load_fixture("bug2_attributeerror_cart.json")
    inc = parse_sentry(payload, path_prefix_strip="")

    expected_dt = datetime.fromtimestamp(1791114000.5, tz=timezone.utc)
    assert inc.occurred_at == expected_dt
    assert inc.release_sha == "9c1d2e3"
    assert inc.exception_type == "AttributeError"
    assert inc.event_count == 22
    assert inc.users_affected == 11
    assert inc.file_path == "services/cart.py"
    assert inc.line_number == 57


def test_edge_library_frame_last():
    payload = _load_fixture("edge_library_frame_last.json")

    # With prefix strip "/app/"
    inc1 = parse_sentry(payload, path_prefix_strip="/app/")
    assert inc1.file_path == "services/inventory.py"
    assert inc1.line_number == 112
    assert inc1.release_sha is None
    assert inc1.occurred_at.tzinfo == timezone.utc

    # With empty prefix strip
    inc2 = parse_sentry(payload, path_prefix_strip="")
    assert inc2.file_path == "app/services/inventory.py"
    assert inc2.line_number == 112


def test_frame_selection_heuristics():
    base_payload = {
        "event_id": "test_evt_1",
        "timestamp": 1728000000,
        "exception": {
            "values": [
                {
                    "type": "RuntimeError",
                    "value": "boom",
                    "stacktrace": {
                        "frames": [
                            {"filename": "site-packages/pkg/core.py", "lineno": 10},
                            {"filename": "app/handlers.py", "lineno": 45},
                            {"filename": "/usr/lib/python3.11/os.py", "lineno": 200},
                        ]
                    },
                }
            ]
        },
    }

    # No in_app flags anywhere but one non-library frame -> that frame is used
    inc = parse_sentry(base_payload, path_prefix_strip="")
    assert inc.file_path == "app/handlers.py"
    assert inc.line_number == 45

    # Only library frames -> ParseError
    only_lib_payload = copy.deepcopy(base_payload)
    only_lib_payload["exception"]["values"][0]["stacktrace"]["frames"] = [
        {"filename": "site-packages/pkg/core.py", "lineno": 10},
        {"filename": "dist-packages/other.py", "lineno": 20},
    ]
    with pytest.raises(ParseError):
        parse_sentry(only_lib_payload, path_prefix_strip="")

    # Chosen frame with lineno 0 -> ParseError
    zero_lineno_payload = copy.deepcopy(base_payload)
    zero_lineno_payload["exception"]["values"][0]["stacktrace"]["frames"] = [
        {"filename": "app/handlers.py", "lineno": 0, "in_app": True}
    ]
    with pytest.raises(ParseError):
        parse_sentry(zero_lineno_payload, path_prefix_strip="")

    # Chosen frame with missing lineno -> ParseError
    missing_lineno_payload = copy.deepcopy(base_payload)
    missing_lineno_payload["exception"]["values"][0]["stacktrace"]["frames"] = [
        {"filename": "app/handlers.py", "in_app": True}
    ]
    with pytest.raises(ParseError):
        parse_sentry(missing_lineno_payload, path_prefix_strip="")


def test_chained_exceptions():
    payload = {
        "event_id": "test_chain",
        "timestamp": 1728000000,
        "exception": {
            "values": [
                {
                    "type": "DatabaseError",
                    "value": "connection lost",
                    "stacktrace": {"frames": [{"filename": "db.py", "lineno": 10, "in_app": True}]},
                },
                {
                    "type": "HTTPInternalServerError",
                    "value": "500 server error",
                    "stacktrace": {"frames": [{"filename": "server.py", "lineno": 99, "in_app": True}]},
                },
            ]
        },
    }
    inc = parse_sentry(payload, path_prefix_strip="")
    assert inc.exception_type == "HTTPInternalServerError"
    assert inc.error_message == "500 server error"
    assert inc.file_path == "server.py"
    assert inc.line_number == 99


@pytest.mark.parametrize(
    ("raw_release", "expected_sha"),
    [
        ("a14b9f2", "a14b9f2"),
        ("a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345", "a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345"),
        ("A14B9F2", "a14b9f2"),
        ("1.2.3", None),
        ("myapp@1.0.0", None),
        ("app@1.0.0+9c1d2e3", "9c1d2e3"),
        ("", None),
        (None, None),
    ],
)
def test_release_sha_table(raw_release, expected_sha):
    payload = {
        "event_id": "test_rel",
        "timestamp": 1728000000,
        "release": raw_release,
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    inc = parse_sentry(payload, path_prefix_strip="")
    assert inc.release_sha == expected_sha


@pytest.mark.parametrize(
    ("raw_ts", "expected_epoch"),
    [
        (1728000000, 1728000000),
        (1728000000.5, 1728000000.5),
        ("1728000000", 1728000000),
        ("2026-10-04T12:00:00Z", 1791115200),
        ("2026-10-04T17:30:00+05:30", 1791115200),
    ],
)
def test_timestamp_parsing_valid(raw_ts, expected_epoch):
    payload = {
        "event_id": "test_ts",
        "timestamp": raw_ts,
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    inc = parse_sentry(payload, path_prefix_strip="")
    assert inc.occurred_at.tzinfo == timezone.utc
    assert inc.occurred_at.timestamp() == expected_epoch


@pytest.mark.parametrize("invalid_ts", [None, "not a date", ""])
def test_timestamp_parsing_invalid(invalid_ts):
    payload = {
        "event_id": "test_ts",
        "timestamp": invalid_ts,
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    with pytest.raises(ParseError):
        parse_sentry(payload, path_prefix_strip="")


def test_counts_precedence():
    # _ichnoscope beats data.issue
    p1 = {
        "_ichnoscope": {"event_count": 50, "users_affected": 25},
        "data": {"issue": {"count": "100", "userCount": "80"}},
        "event_id": "c1",
        "timestamp": 1728000000,
        "exception": {
            "values": [
                {
                    "type": "TypeError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    inc1 = parse_sentry(p1, path_prefix_strip="")
    assert inc1.event_count == 50
    assert inc1.users_affected == 25

    # data.issue numeric strings become ints
    p2 = {
        "data": {"issue": {"count": "57", "userCount": "9"}},
        "event_id": "c2",
        "timestamp": 1728000000,
        "exception": {
            "values": [
                {
                    "type": "TypeError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    inc2 = parse_sentry(p2, path_prefix_strip="")
    assert inc2.event_count == 57
    assert inc2.users_affected == 9

    # Non-numeric fallback to defaults (1, 0)
    p3 = {
        "data": {"issue": {"count": "invalid", "userCount": "none"}},
        "event_id": "c3",
        "timestamp": 1728000000,
        "exception": {
            "values": [
                {
                    "type": "TypeError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    inc3 = parse_sentry(p3, path_prefix_strip="")
    assert inc3.event_count == 1
    assert inc3.users_affected == 0

    # event_count 0 clamps to 1
    p4 = {
        "_ichnoscope": {"event_count": 0, "users_affected": -5},
        "event_id": "c4",
        "timestamp": 1728000000,
        "exception": {
            "values": [
                {
                    "type": "TypeError",
                    "value": "err",
                    "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                }
            ]
        },
    }
    inc4 = parse_sentry(p4, path_prefix_strip="")
    assert inc4.event_count == 1
    assert inc4.users_affected == 0


def test_parsing_errors():
    # Non-dict payload
    with pytest.raises(ParseError):
        parse_sentry("not a dict", path_prefix_strip="")  # type: ignore[arg-type]

    # No exception
    with pytest.raises(ParseError):
        parse_sentry({"event_id": "e1", "timestamp": 1728000000}, path_prefix_strip="")

    # Empty values
    with pytest.raises(ParseError):
        parse_sentry(
            {"event_id": "e2", "timestamp": 1728000000, "exception": {"values": []}},
            path_prefix_strip="",
        )

    # Missing type
    with pytest.raises(ParseError):
        parse_sentry(
            {
                "event_id": "e3",
                "timestamp": 1728000000,
                "exception": {
                    "values": [
                        {
                            "value": "no type",
                            "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                        }
                    ]
                },
            },
            path_prefix_strip="",
        )

    # Missing event_id
    with pytest.raises(ParseError):
        parse_sentry(
            {
                "timestamp": 1728000000,
                "exception": {
                    "values": [
                        {
                            "type": "ValueError",
                            "value": "err",
                            "stacktrace": {"frames": [{"filename": "main.py", "lineno": 1, "in_app": True}]},
                        }
                    ]
                },
            },
            path_prefix_strip="",
        )


def test_parse_purity():
    orig_payload = _load_fixture("bug1_keyerror_payment.json")
    payload_copy = copy.deepcopy(orig_payload)
    _ = parse_sentry(orig_payload, path_prefix_strip="/app/")
    assert orig_payload == payload_copy


def test_settings_default_path_prefix(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("PATH_PREFIX_STRIP", "/app")
    get_settings.cache_clear()

    payload = _load_fixture("edge_library_frame_last.json")
    # Calling parse_sentry without path_prefix_strip uses get_settings().path_prefix_strip
    inc = parse_sentry(payload)
    assert inc.file_path == "services/inventory.py"
    assert inc.line_number == 112

    get_settings.cache_clear()
