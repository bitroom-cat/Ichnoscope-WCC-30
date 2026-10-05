"""Unit tests for backend/ichnoscope/blame.py."""

from datetime import datetime, timezone

import httpx
import pytest
from ichnoscope.blame import (
    BlameResult,
    commit_at_line,
    find_culprit,
)
from ichnoscope.config import load_settings
from ichnoscope.models import Incident


def _make_incident(**kwargs) -> Incident:
    base = {
        "incident_id": "test-inc-456",
        "occurred_at": datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
        "exception_type": "KeyError",
        "error_message": "'stripe_token'",
        "file_path": "services/payment.py",
        "line_number": 84,
        "stack_excerpt": "line 84 in charge_card",
        "environment": "production",
        "release_sha": "a14b9f2c7d3e5f60718293a4b5c6d7e8f9012345",
    }
    base.update(kwargs)
    return Incident(**base)


def test_commit_at_line():
    ranges = [
        {"startingLine": 1, "endingLine": 50, "commit": {"oid": "111"}},
        {"startingLine": 60, "endingLine": 100, "commit": {"oid": "222"}},
    ]
    # Within range
    assert commit_at_line(ranges, 25) == {"oid": "111"}
    # Boundaries
    assert commit_at_line(ranges, 1) == {"oid": "111"}
    assert commit_at_line(ranges, 50) == {"oid": "111"}
    assert commit_at_line(ranges, 60) == {"oid": "222"}
    assert commit_at_line(ranges, 100) == {"oid": "222"}
    # Gap between ranges
    assert commit_at_line(ranges, 55) is None
    # Outside ranges
    assert commit_at_line(ranges, 0) is None
    assert commit_at_line(ranges, 105) is None
    assert commit_at_line([], 10) is None


def test_stub_mode():
    incident = _make_incident()
    settings = load_settings({
        "USE_STUB_GITHUB": "true",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "FALLBACK_ASSIGNEE": "fallback-dev",
    })

    def forbidden(request: httpx.Request) -> httpx.Response:
        pytest.fail("Network must not be called in stub mode")

    client = httpx.Client(transport=httpx.MockTransport(forbidden))
    result = find_culprit(incident, settings=settings, client=client)

    assert isinstance(result, BlameResult)
    assert result.source == "stub"
    assert result.culprit is not None
    assert result.culprit.author_login == "fallback-dev"
    assert result.culprit.sha == "d3e5f60718293a4b5c6d7e8f9012345a14b9f2c7"
    assert "services/payment.py" in result.culprit.diff
    assert result.culprit.confidence == "high"
    assert result.culprit.within_window is True


def test_graphql_blame_success():
    incident = _make_incident(line_number=84)
    sha_blamed = "d3e5f60718293a4b5c6d7e8f9012345a14b9f2c7"

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "graphql" in url_str:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "repository": {
                            "object": {
                                "blame": {
                                    "ranges": [
                                        {
                                            "startingLine": 80,
                                            "endingLine": 90,
                                            "commit": {
                                                "oid": sha_blamed,
                                                "message": "Refactor payment",
                                                "committedDate": "2026-10-04T10:00:00Z",
                                                "author": {
                                                    "name": "Pat Engineer",
                                                    "user": {"login": "pat-eng"},
                                                },
                                                "associatedPullRequests": {
                                                    "nodes": [
                                                        {"number": 482, "author": {"login": "pat-pr-login"}}
                                                    ]
                                                },
                                            },
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
            )
        if f"/commits/{sha_blamed}" in url_str:
            return httpx.Response(
                200,
                json={
                    "files": [
                        {
                            "filename": "services/payment.py",
                            "patch": "@@ -80,4 +80,4 @@\n- old_code\n+ new_code\n",
                        }
                    ]
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "USE_STUB_GITHUB": "false",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "GITHUB_TOKEN": "test-pat-token",
    })

    result = find_culprit(incident, settings=settings, client=client)

    assert result.source == "blame"
    assert result.culprit is not None
    assert result.culprit.sha == sha_blamed
    assert result.culprit.author_login == "pat-pr-login"
    assert result.culprit.pr_number == 482
    assert result.culprit.confidence == "high"
    assert result.culprit.within_window is True
    assert "+ new_code" in result.culprit.diff


def test_blame_gap_falls_back_to_recent_commits():
    # Line 84 is not in blame ranges
    incident = _make_incident(line_number=84)

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "graphql" in url_str:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "repository": {
                            "object": {
                                "blame": {
                                    "ranges": [
                                        {"startingLine": 1, "endingLine": 50, "commit": {"oid": "aaa"}}
                                    ]
                                }
                            }
                        }
                    }
                },
            )
        if "/commits" in url_str and "commits/" not in url_str:
            return httpx.Response(
                200,
                json=[
                    {
                        "sha": "fb11111111111111111111111111111111111111",
                        "commit": {
                            "message": "Recent change 1",
                            "author": {"name": "Alice", "date": "2026-10-04T09:00:00Z"},
                        },
                        "author": {"login": "alice-login"},
                    },
                    {
                        "sha": "fb22222222222222222222222222222222222222",
                        "commit": {
                            "message": "Recent change 2",
                            "author": {"name": "Bob", "date": "2026-10-03T09:00:00Z"},
                        },
                        "author": {"login": "bob-login"},
                    },
                ],
            )
        if "/commits/fb111111" in url_str:
            return httpx.Response(
                200,
                json={
                    "files": [
                        {
                            "filename": "services/payment.py",
                            "patch": "@@ -1,1 +1,1 @@\n+ patch 1",
                        }
                    ]
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = load_settings({
        "USE_STUB_GITHUB": "false",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "GITHUB_TOKEN": "test-pat-token",
    })

    result = find_culprit(incident, settings=settings, client=client)

    assert result.source == "fallback"
    assert result.culprit is not None
    assert result.culprit.sha.startswith("fb111")
    assert result.culprit.author_login == "alice-login"
    assert result.culprit.confidence == "low"
    assert len(result.other_commits) == 1
    assert result.other_commits[0].sha.startswith("fb222")


def test_unconfigured_repository():
    incident = _make_incident()
    settings = load_settings({
        "USE_STUB_GITHUB": "false",
        "GITHUB_REPOSITORY": None,
    })

    result = find_culprit(incident, settings=settings)
    assert result.source == "none"
    assert result.culprit is None
    assert "not configured" in (result.error or "")
