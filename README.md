# Ichnoscope

Ichnoscope is an incident-triage system that follows the evidence left in a deployed codebase. It accepts Sentry errors, finds the commit associated with the failing line, explains the likely failure, and prepares a useful GitHub issue.

The goal is to reduce the time engineers spend assembling incident context. Ichnoscope is a triage assistant, not an auto-remediation system: it does not change code, open pull requests, or deploy fixes.

## How It Works

The documented MVP follows a deterministic pipeline, with an LLM used only to explain evidence gathered by code:

1. **Receive:** accept a Sentry event through a signed webhook, or replay a saved fixture for local testing and demos.
2. **Deduplicate:** fingerprint events by exception type, repository-relative file path, and line number. Repeated open incidents update the existing issue instead of creating an issue for every event; a recurrence after closure is treated as a regression.
3. **Parse:** convert the Sentry payload into an incident. Use the last in-application stack frame and strip any configured container path prefix.
4. **Find a suspect:** query GitHub blame at the event's release SHA, then collect the associated commit and diff. If blame is inconclusive, inspect the three latest commits on the file and mark the result low-confidence.
5. **Explain:** provide bounded incident and code evidence to one LLM call. The structured explanation contains a domain, a root-cause hypothesis, and exactly three verification steps.
6. **Set severity and dispatch:** calculate severity with deterministic thresholds, select an assignable owner or configured fallback, and create a labeled GitHub issue. Slack notification is optional and best-effort.

If the LLM is unavailable, the pipeline still produces a useful issue using a fallback template. GitHub failures are retried; an inconclusive blame result is identified as low-confidence rather than presented as certainty.

## Architecture And Status

The detailed technical specification and the existing architecture diagram describe the original backend-first MVP: SQLite-backed deduplication and direct issue creation after triage. The repository has also been scaffolded toward a dashboard deployment: a FastAPI backend, hosted Postgres, and a Next.js admin UI, with a draft-and-approve publishing flow.

These are two stages of the design, not interchangeable implementations. The dashboard/Postgres approval flow is the newer deployment direction, but the technical specification and architecture diagram have not yet been updated to match it. The files in `backend/` and `web/` are currently placeholders, so there is no runnable pipeline or dashboard yet. Resolve this design difference before implementing persistence and publishing behavior.

For the planned dashboard deployment:

- The Next.js frontend is intended for Vercel; the FastAPI service runs on a Python web host.
- Postgres is the shared store for runs, logs, settings, and repository configuration. Local development may use Docker Compose with Postgres.
- The browser does not receive the admin token or provider credentials. Next.js server routes proxy requests to the backend using the admin token.
- The pipeline stores a draft issue for an administrator to approve or reject. Run logs are polled by the dashboard rather than streamed over websockets.
- Free hosting tiers may sleep or have storage limits; check provider limits and wake the backend before a demo.

## Design And Safety

- **Evidence before explanation:** deterministic code finds the commit, author, and severity. The LLM does not choose SHAs, usernames, or severity.
- **Bounded model access:** the LLM receives a limited evidence bundle and has no tools or write access. Treat error text, stack traces, and commit messages as untrusted data.
- **Least privilege:** scope GitHub credentials to the target repository and redact secrets and personal data before posting content.
- **Prompt response:** verify the Sentry HMAC signature and acknowledge valid events before background processing.
- **Graceful degradation:** blame, model, and notification failures should produce a lower-confidence or simpler result rather than silently dropping an incident.
- **Human authority:** Ichnoscope reports a suspect, not a proven culprit. The planned dashboard adds human approval before publishing an issue.

## Repository Layout

```text
.
├── backend/                 FastAPI service and incident pipeline placeholders
│   ├── ichnoscope/          Configuration, models, storage, pipeline, and API modules
│   ├── fixtures/            Saved Sentry payloads and cached model responses
│   ├── bench/               Benchmark runner and results
│   └── tests/               Backend tests
├── docs/                    Architecture, technical specification, and demo notes
└── web/                     Next.js dashboard placeholders
```

The demo application used to create planted bugs is a separate repository. Keep its fixtures or test code separate from this service unless a later design decision says otherwise.

## Configuration Plan

The backend will need credentials and settings supplied through its environment, not committed to the repository. The original MVP specification names:

| Variable | Purpose |
| --- | --- |
| `GITHUB_TOKEN` | Repository-scoped GitHub API access for blame, diffs, and issues |
| `GITHUB_REPOSITORY` | Target repository in `owner/name` form |
| `SENTRY_CLIENT_SECRET` | Verify the Sentry webhook signature |
| `LLM_API_KEY`, `LLM_MODEL` | Configure the MVP explanation provider |
| `PATH_PREFIX_STRIP` | Optional container-path prefix to remove from stack frames |
| `FALLBACK_ASSIGNEE` | Assignable user used when no suitable suspect is available |
| `SLACK_WEBHOOK_URL` | Optional best-effort notification destination |
| `DRY_RUN` | Print the issue draft without publishing it |

The dashboard deployment additionally expects backend URL, admin token, and dashboard password configuration. Keep the admin token server-side; never put GitHub or LLM credentials in Vercel or browser-visible variables. See the technical specification and deployment configuration before wiring environment names, since the MVP and dashboard plans currently differ.

Do not commit real secrets. Use the environment example files as placeholders once their variable names are finalized.

## Development And Validation

This repository currently contains the project documentation and a directory scaffold, not an executable application. Dependencies, startup commands, and tests will be documented here when the backend and frontend implementations are added.

The MVP validation plan in the technical specification includes:

- Unit tests for Sentry parsing, blame line boundaries, severity thresholds, stable fingerprints, signature validation, and redaction.
- Integration tests for issue creation, LLM fallback, low-confidence blame, duplicate event storms, and closed-issue regressions.
- A benchmark using ten planted bugs, measuring blame accuracy, time to issue, duplicate suppression, and manual triage time.

The stated targets are at least 8 correct blamed commits out of 10, under 60 seconds from event to issue excluding LLM outages, and one issue for 50 identical events.

## Documentation

- [Architecture diagram](docs/architecture.md)
- [Technical specification](docs/ICHNOSCOPE_TECHNICAL_SPEC%20(1).md)
- [Dashboard architecture notes](docs/TECHNICAL_SPEC.md)
- [Demo script](docs/demo_script.md)

The dashboard architecture notes are currently a placeholder. Update them together with the existing technical specification when the Postgres and approval workflow is finalized.