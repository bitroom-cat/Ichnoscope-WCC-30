"""Unit tests for backend/ichnoscope/notify.py."""

import json

import httpx
from ichnoscope.config import load_settings
from ichnoscope.notify import notify_slack


def test_notify_slack_success():
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(200, text="ok")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    url = "https://hooks.slack.com/services/T00/B00/X00000000000"

    ok = notify_slack(
        title="KeyError: 'stripe_token'",
        severity="P1-Critical",
        assignee="pat-eng",
        issue_url="https://github.com/owner/repo/issues/42",
        webhook_url=url,
        client=client,
    )

    assert ok is True
    assert len(recorded) == 1
    req = recorded[0]
    data = json.loads(req.content)
    assert "KeyError" in data["text"]
    assert "P1-Critical" in data["text"]
    assert "https://github.com/owner/repo/issues/42" in data["text"]


def test_notify_slack_unconfigured():
    settings = load_settings({"SLACK_WEBHOOK_URL": None})
    ok = notify_slack(
        title="Test Error",
        severity="P3-Medium",
        assignee=None,
        issue_url="https://github.com/owner/repo/issues/1",
        settings=settings,
    )
    assert ok is False


def test_notify_slack_failure_gracefully_handled():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Slack server error")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ok = notify_slack(
        title="Test Error",
        severity="P2-High",
        assignee="octocat",
        issue_url="https://github.com/owner/repo/issues/2",
        webhook_url="https://hooks.slack.com/services/T/B/X",
        client=client,
    )
    assert ok is False


def test_notify_slack_redaction():
    recorded: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(200, text="ok")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fake_token = "gh" + "p_" + "A" * 36

    notify_slack(
        title=f"Crash with token {fake_token}",
        severity="P2-High",
        assignee="octocat",
        issue_url="https://github.com/owner/repo/issues/3",
        webhook_url="https://hooks.slack.com/services/T/B/X",
        client=client,
    )

    data = json.loads(recorded[0].content)
    assert fake_token not in data["text"]
    assert "[REDACTED:github_token]" in data["text"]
