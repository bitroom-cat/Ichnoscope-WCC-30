"""GitHub issue draft rendering for incident reports with prompt injection and mention defenses."""

import re
from datetime import datetime

from pydantic import BaseModel

from ichnoscope.models import Culprit, Explanation, Incident, Severity
from ichnoscope.redact import redact

FP_PATTERN = re.compile(r"^[0-9a-f]{12}$")
MENTION_PATTERN = re.compile(r"@(?=[a-zA-Z0-9_-])")


class IssueDraft(BaseModel):
    """Structured draft of a GitHub issue to be reviewed or dispatched."""

    title: str
    body: str
    labels: list[str]
    suggested_owner: str | None
    assign_recommended: bool


def _neutralize_untrusted_text(text: str) -> str:
    """Neutralize potential mentions and HTML comment injection in untrusted text."""
    if not text:
        return ""
    # 1. Insert zero-width space after @ followed by word character to disarm mentions
    t = MENTION_PATTERN.sub("@\u200b", text)
    # 2. Escape HTML comments so user input cannot forge or corrupt fingerprint markers
    t = t.replace("<!--", "&lt;!--").replace("-->", "--&gt;")
    return t


def _neutralize_llm_text(text: str) -> str:
    """Neutralize mentions, HTML comments, and markdown image injections in LLM text."""
    t = _neutralize_untrusted_text(text)
    # 3. Disarm markdown images to block tracking pixels / exfiltration
    return t.replace("![", r"!\[")


def _single_line(text: str, max_len: int | None = None) -> str:
    """Collapse all whitespace and newlines to a single space, optionally truncated."""
    collapsed = " ".join(text.split())
    if max_len is not None and len(collapsed) > max_len:
        return collapsed[:max_len]
    return collapsed


def _wrap_long_lines(text: str, max_line_len: int = 500) -> str:
    """Wrap excessively long unbroken lines to prevent pathological regex backtracking."""
    if not text:
        return ""
    lines = text.splitlines()
    wrapped_lines: list[str] = []
    for line in lines:
        if len(line) > max_line_len:
            for i in range(0, len(line), max_line_len):
                wrapped_lines.append(line[i : i + max_line_len])
        else:
            wrapped_lines.append(line)
    return "\n".join(wrapped_lines)


def _make_fence(text: str, lang: str = "") -> str:
    """Wrap content in a markdown fence longer than any backtick sequence inside."""
    backtick_runs = re.findall(r"`+", text)
    max_run = max((len(r) for r in backtick_runs), default=0)
    fence_len = max(3, max_run + 1)
    fence = "`" * fence_len
    return f"{fence}{lang}\n{text}\n{fence}"


def _humanize_duration(occurred_at: datetime, committed_at: datetime, within_window: bool) -> str:
    """Compute human-friendly elapsed time between suspect commit and error occurrence."""
    delta = occurred_at - committed_at
    total_seconds = delta.total_seconds()

    if total_seconds < 0:
        return "after this error was recorded (check the release SHA and clocks)"

    if total_seconds < 60:
        time_text = "less than a minute"
    elif total_seconds < 120 * 60:
        mins = int(total_seconds // 60)
        time_text = f"{mins} minute" if mins == 1 else f"{mins} minutes"
    elif total_seconds < 48 * 3600:
        hrs = int(total_seconds // 3600)
        time_text = f"{hrs} hour" if hrs == 1 else f"{hrs} hours"
    else:
        days = int(total_seconds // 86400)
        time_text = f"{days} day" if days == 1 else f"{days} days"

    qualifier = (
        "(recent change, likely regression)"
        if within_window
        else "(older code, likely triggered by new data or an upstream change)"
    )
    return f"{time_text} before this error {qualifier}"


def extract_fingerprint(body: str) -> str | None:
    """Read the hidden ichnoscope fingerprint marker back out of an issue body."""
    lines = body.splitlines()
    in_fence = False
    fence_delim = ""

    for line in lines:
        stripped = line.strip()
        # Track multi-backtick code fences
        if stripped.startswith("```"):
            m = re.match(r"^(`{3,})", stripped)
            if m:
                delim = m.group(1)
                if not in_fence:
                    in_fence = True
                    fence_delim = delim
                elif fence_delim in stripped:
                    in_fence = False
                    fence_delim = ""
            continue

        if not in_fence:
            m = re.search(r"<!--\s*ichnoscope:fp=([0-9a-f]{12})\s*-->", line)
            if m:
                return m.group(1)

    return None


def build_issue_draft(
    incident: Incident,
    culprit: Culprit | None,
    explanation: Explanation | None,
    severity: Severity,
    severity_reason: str,
    fingerprint: str,
    *,
    is_regression: bool = False,
    previous_issue_number: int | None = None,
    repo: str | None = None,
    fallback_assignee: str | None = None,
) -> IssueDraft:
    """Turn triage evidence into a safe, formatted GitHub Issue draft."""
    if fingerprint and not FP_PATTERN.match(fingerprint):
        raise ValueError(f"fingerprint must be empty or a 12-char lowercase hex string, got '{fingerprint}'")

    # Title assembly: [P1-Critical] KeyError in services/payment.py
    raw_title = f"[{severity}] {incident.exception_type} in {incident.file_path}"
    title_single = _single_line(raw_title)
    if len(title_single) > 120:
        title = title_single[:119] + "…"
    else:
        title = title_single

    # Determine suggested owner and recommendation
    possible_author_line = ""
    if culprit is not None and culprit.confidence == "high" and culprit.author_login:
        suggested_owner = culprit.author_login
        owner_text = f"@{culprit.author_login}"
        assign_recommended = True
    elif culprit is not None and culprit.author_login:
        # Low confidence with author login: do not mention; show as code block
        safe_login = _single_line(_neutralize_untrusted_text(culprit.author_login))
        possible_author_line = f"**Possible author (low confidence):** `{safe_login}`\n"
        if fallback_assignee:
            suggested_owner = fallback_assignee
            owner_text = f"@{fallback_assignee} (on-call fallback)"
            assign_recommended = True
        else:
            suggested_owner = None
            owner_text = "unassigned"
            assign_recommended = False
    elif fallback_assignee:
        suggested_owner = fallback_assignee
        owner_text = f"@{fallback_assignee} (on-call fallback)"
        assign_recommended = True
    else:
        suggested_owner = None
        owner_text = "unassigned"
        assign_recommended = False

    # Labels assembly
    labels: list[str] = ["ichnoscope"]
    if explanation is not None:
        labels.append(f"domain:{explanation.domain}")
    labels.append(f"severity:{severity}")
    if is_regression or (culprit is not None and culprit.within_window):
        labels.append("regression")
    if culprit is None or culprit.confidence == "low":
        labels.append("low-confidence")
    if explanation is None:
        labels.append("analysis-unavailable")
    # Preserve ordering without duplicates
    labels = list(dict.fromkeys(labels))

    # Neutralize text components
    safe_exc_type = _single_line(_neutralize_untrusted_text(incident.exception_type))
    safe_error_msg = _single_line(_neutralize_untrusted_text(incident.error_message), max_len=200)
    domain_str = f"`{explanation.domain}`" if explanation is not None else "unknown"
    confidence_str = culprit.confidence if culprit is not None else "low"

    # Header section
    header_parts = [
        f"## [Auto-triage] {safe_exc_type}: {safe_error_msg}\n",
        f"**Severity:** {severity} ({severity_reason})  **Domain:** {domain_str}  **Confidence:** {confidence_str}",
        f"**Failing line:** `{incident.file_path}:{incident.line_number}`",
        f"**Suggested owner:** {owner_text}",
    ]
    if possible_author_line:
        header_parts.append(possible_author_line.rstrip())

    # Suspect commit & Last changed metadata
    if culprit is not None:
        first_line_msg = _single_line(_neutralize_untrusted_text(culprit.message.splitlines()[0] if culprit.message else ""))
        sha_short = culprit.sha[:7]
        pr_part = f" (PR #{culprit.pr_number})" if culprit.pr_number is not None else ""
        if repo:
            commit_link = f"[{sha_short}](https://github.com/{repo}/commit/{culprit.sha})"
        else:
            commit_link = sha_short
        header_parts.append(f"**Suspect commit:** {commit_link}{pr_part}: {first_line_msg}")
        last_changed_text = _humanize_duration(incident.occurred_at, culprit.committed_at, culprit.within_window)
        header_parts.append(f"**Last changed:** {last_changed_text}")
    else:
        header_parts.append("No suspect commit could be identified for this line.")

    if previous_issue_number is not None:
        header_parts.append(f"**Previously reported in:** #{previous_issue_number} (reopened as a regression)")

    # Size guard pre-truncation budget: body limit is 60,000 characters
    diff_raw = culprit.diff if culprit is not None else ""
    stack_raw = incident.stack_excerpt

    # If diff or stack are enormous (e.g. 100k+ bypass objects), truncate them initially to 24k
    if len(diff_raw) > 24_000:
        diff_raw = diff_raw[:24_000] + "\n... [truncated]"
    if len(stack_raw) > 24_000:
        stack_raw = stack_raw[:24_000] + "\n... [truncated]"

    # Wrap long lines in diff and stack excerpt
    diff_wrapped = _wrap_long_lines(diff_raw)
    stack_wrapped = _wrap_long_lines(stack_raw)

    def _assemble_body(d_content: str, s_content: str) -> str:
        sections: list[str] = ["\n".join(header_parts)]

        # Analysis section
        if explanation is not None:
            safe_hypothesis = _neutralize_llm_text(explanation.root_cause_hypothesis)
            sections.append(f"### Why it probably failed\n{safe_hypothesis}")
        else:
            safe_stack = _neutralize_untrusted_text(s_content)
            fenced_stack = _make_fence(safe_stack)
            sections.append(
                f"### Automated analysis unavailable\nAutomated analysis was unavailable for this incident. The raw evidence is below.\n\n### Stack excerpt\n{fenced_stack}"
            )

        # Suspect change diff section
        if culprit is not None:
            if d_content and d_content.strip():
                safe_diff = _neutralize_untrusted_text(d_content)
                fenced_diff = _make_fence(safe_diff, lang="diff")
            else:
                fenced_diff = "_No diff available._"
            sections.append(f"### Suspect change\n{fenced_diff}")

        # Checklist section
        if explanation is not None:
            checklist_lines = ["### Verification checklist"]
            for item in explanation.checklist:
                clean_item = _single_line(_neutralize_llm_text(item), max_len=300)
                checklist_lines.append(f"- [ ] {clean_item}")
            sections.append("\n".join(checklist_lines))

        # Footer
        footer_text = "---\n_Drafted by Ichnoscope. This is a suspect, not a verdict: blame shows who last touched the line, not who is at fault._"
        if fingerprint:
            footer_text += f"\n<!-- ichnoscope:fp={fingerprint} -->"

        sections.append(footer_text)
        return "\n\n".join(sections)

    full_body = _assemble_body(diff_wrapped, stack_wrapped)

    # Size guard loop: guarantee full_body <= 60,000 characters
    while len(full_body) > 60_000:
        overage = len(full_body) - 58_000
        if culprit is not None and len(diff_wrapped) > 1000:
            cut_amount = min(overage, len(diff_wrapped) - 500)
            diff_wrapped = diff_wrapped[:-cut_amount] + "\n... [truncated]"
        elif len(stack_wrapped) > 1000:
            cut_amount = min(overage, len(stack_wrapped) - 500)
            stack_wrapped = stack_wrapped[:-cut_amount] + "\n... [truncated]"
        else:
            break
        full_body = _assemble_body(diff_wrapped, stack_wrapped)

    # Defense in depth: sanitize final body with redact()
    sanitized_body = redact(full_body)

    return IssueDraft(
        title=title,
        body=sanitized_body,
        labels=labels,
        suggested_owner=suggested_owner,
        assign_recommended=assign_recommended,
    )
