"""Unit tests for backend/ichnoscope/publisher.py."""

import json
from datetime import datetime, timezone

import httpx
import pytest
from ichnoscope.config import load_settings
from ichnoscope.models import Culprit, Explanation, Incident
from ichnoscope.publisher import (
    check_assignable,
    publish_issue,
    publish_repeat_comment,
)


def _make_incident(**kwargs) -> Incident:
    base = {
        "incident_id": "inc-pub-1",
        "occurred_at": datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
        "exception_type": "KeyError",
        "error_message": "'stripe_token'",
        "file_path": "services/payment.py",
        "line_number": 84,
        "stack_excerpt": "line 84 in charge_card",
    }
    base.update(kwargs)
    return Incident(**base)


def _make_culprit(**kwargs) -> Culprit:
    base = {
        "sha": "d3e5f60718293a4b5c6d7e8f9012345a14b9f2c7",
        "author_login": "pat-eng",
        "author_name": "Pat Engineer",
        "message": "Refactor payment",
        "committed_at": datetime(2026, 10, 4, 10, 0, 0, tzinfo=timezone.utc),
        "within_window": True,
        "confidence": "high",
        "diff": "@@ -1 +1 @@\n+ patch\n",
    }
    base.update(kwargs)
    return Culprit(**base)


def test_check_assignable():
    def handler(request: httpx.Request) -> httpx.Response:
        if "octocat" in str(request.url):
            return httpx.Response(204)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert check_assignable(client, "owner", "repo", "octocat", "token") is True
    assert check_assignable(client, "owner", "repo", "unknown-user", "token") is False


def test_publish_issue_dry_run():
    incident = _make_incident()
    culprit = _make_culprit()
    explanation = Explanation(
        domain="backend",
        root_cause_hypothesis="Hypothesis text.",
        checklist=["Step 1", "Step 2", "Step 3"],
    )
    settings = load_settings({
        "DRY_RUN": "true",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "FALLBACK_ASSIGNEE": "octocat",
    })

    def forbidden(request: httpx.Request) -> httpx.Response:
        pytest.fail("Network call forbidden in dry run")

    client = httpx.Client(transport=httpx.MockTransport(forbidden))

    result = publish_issue(
        incident=incident,
        culprit=culprit,
        explanation=explanation,
        severity="P2-High",
        settings=settings,
        client=client,
    )

    assert result.issue_number == 999
    assert "https://github.com/testowner/testrepo/issues/999" in result.issue_url
    assert "severity:P2-High" in result.labels
    assert "domain:backend" in result.labels


def test_publish_issue_live_success():
    incident = _make_incident()
    culprit = _make_culprit(author_login="pat-eng")
    explanation = Explanation(
        domain="backend",
        root_cause_hypothesis="Hypothesis text.",
        checklist=["Step 1", "Step 2", "Step 3"],
    )
    settings = load_settings({
        "DRY_RUN": "false",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "GITHUB_TOKEN": "test-pat-token",
        "FALLBACK_ASSIGNEE": "octocat",
    })

    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        url_str = str(request.url)
        if "/assignees/pat-eng" in url_str:
            return httpx.Response(204)
        if "/issues" in url_str:
            return httpx.Response(
                201,
                json={
                    "number": 123,
                    "html_url": "https://github.com/testowner/testrepo/issues/123",
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = publish_issue(
        incident=incident,
        culprit=culprit,
        explanation=explanation,
        severity="P1-Critical",
        settings=settings,
        client=client,
    )

    assert result.issue_number == 123
    assert result.issue_url == "https://github.com/testowner/testrepo/issues/123"
    assert result.assignee == "pat-eng"

    issue_req = next(r for r in recorded if r.method == "POST")
    body = json.loads(issue_req.content)
    assert "[P1-Critical] KeyError" in body["title"]
    assert "severity:P1-Critical" in body["labels"]
    assert body["assignees"] == ["pat-eng"]


def test_publish_issue_fallback_when_not_assignable():
    incident = _make_incident()
    culprit = _make_culprit(author_login="unregistered-bot")
    settings = load_settings({
        "DRY_RUN": "false",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "GITHUB_TOKEN": "test-pat-token",
        "FALLBACK_ASSIGNEE": "octocat",
    })

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "/assignees/unregistered-bot" in url_str:
            return httpx.Response(404)
        if "/assignees/octocat" in url_str:
            return httpx.Response(204)
        if "/issues" in url_str:
            return httpx.Response(
                201,
                json={
                    "number": 124,
                    "html_url": "https://github.com/testowner/testrepo/issues/124",
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = publish_issue(
        incident=incident,
        culprit=culprit,
        explanation=None,
        severity="P3-Medium",
        settings=settings,
        client=client,
    )

    assert result.assignee == "octocat"
    assert result.issue_number == 124


def test_publish_repeat_comment():
    settings = load_settings({
        "DRY_RUN": "false",
        "GITHUB_REPOSITORY": "testowner/testrepo",
        "GITHUB_TOKEN": "test-pat-token",
    })

    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(201, json={"id": 9999})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ok = publish_repeat_comment(123, 5, settings=settings, client=client)

    assert ok is True
    assert len(recorded) == 1
    assert "/issues/123/comments" in str(recorded[0].url)
    data = json.loads(recorded[0].content)
    assert "Seen 5 more times" in data["body"]
