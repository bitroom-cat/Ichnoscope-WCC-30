"""Pure Sentry error event parser converting incoming webhook/fixture payloads into Incident data models."""

import re
from datetime import datetime, timezone
from typing import Any

from ichnoscope.models import Incident

LIB_SUBSTRINGS: tuple[str, ...] = (
    "site-packages",
    "dist-packages",
    "node_modules",
    "/usr/lib/",
    "<frozen",
)


class ParseError(ValueError):
    """Raised when a Sentry payload is invalid, malformed, or missing required fields."""


def _find_event(payload: dict) -> dict:
    """Locate the event dictionary containing an exception in the payload envelope."""
    if "exception" in payload and isinstance(payload["exception"], dict):
        return payload

    data = payload.get("data")
    if isinstance(data, dict):
        event = data.get("event")
        if isinstance(event, dict) and "exception" in event and isinstance(event["exception"], dict):
            return event
        error = data.get("error")
        if isinstance(error, dict) and "exception" in error and isinstance(error["exception"], dict):
            return error

    raise ParseError("no event with an exception found")


def _is_library_frame(frame: dict) -> bool:
    """Determine whether a stack frame originates from third-party/system libraries."""
    if frame.get("in_app") is False:
        return True
    path = str(frame.get("filename") or frame.get("abs_path") or "")
    return any(lib in path for lib in LIB_SUBSTRINGS)


def _normalize_frame_path(path: str, path_prefix_strip: str) -> str:
    """Normalize file path by stripping schemes, path prefixes, and leading slashes."""
    p = path.strip()
    if p.startswith("app:///"):
        p = p[len("app:///"):].strip()
    p = p.replace("\\", "/")
    if path_prefix_strip and p.startswith(path_prefix_strip):
        p = p[len(path_prefix_strip):]
    while p.startswith(("./", "/")):
        if p.startswith("./"):
            p = p[2:]
        elif p.startswith("/"):
            p = p[1:]
    return p


def _pick_failing_frame(frames: list[dict]) -> dict:
    """Select the crash site application frame using in_app flags and library heuristics."""
    # 1. The last frame with in_app true
    for f in reversed(frames):
        if isinstance(f, dict) and f.get("in_app") is True:
            return f

    # 2. If no frame has in_app true, use the last frame without library substrings
    for f in reversed(frames):
        if isinstance(f, dict) and not _is_library_frame(f):
            return f

    # 3. Otherwise raise ParseError
    raise ParseError("no application frame in stack trace")


def _parse_timestamp(event: dict) -> datetime:
    """Parse event timestamp (epoch number/numeric-string or ISO-8601) to UTC datetime."""
    raw = event.get("timestamp")
    if raw is None:
        raw = event.get("datetime")
    if raw is None:
        raise ParseError("missing timestamp or datetime in event")

    # Numeric timestamp (int or float)
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        except (ValueError, OSError) as err:
            raise ParseError(f"invalid timestamp: {raw}") from err

    # String timestamp
    if isinstance(raw, str):
        trimmed = raw.strip()
        if not trimmed:
            raise ParseError("empty timestamp in event")
        # Try numeric string
        try:
            val = float(trimmed)
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except ValueError:
            pass

        # Try ISO-8601 string
        iso_str = trimmed
        if iso_str.endswith(("Z", "z")):
            iso_str = iso_str[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, OSError) as err:
            raise ParseError(f"invalid timestamp string: '{trimmed}'") from err

    raise ParseError(f"unsupported timestamp format: {type(raw)}")


def _parse_release_sha(event: dict) -> str | None:
    """Extract release commit SHA from release string, returning lowercase 7-40 hex or None."""
    raw = event.get("release")
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None

    hex_pattern = r"^[0-9a-fA-F]{7,40}$"
    if re.match(hex_pattern, s):
        return s.lower()

    # Match part after last '@' or '+'
    parts = re.split(r"[@+]", s)
    candidate = parts[-1]
    if re.match(hex_pattern, candidate):
        return candidate.lower()

    return None


def _parse_count_val(val: Any) -> int | None:
    """Parse numeric count value or return None if non-numeric."""
    if val is None:
        return None
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def _build_stack_excerpt(frames: list[dict], path_prefix_strip: str, exc_type: str, exc_value: str) -> str:
    """Build formatted stack excerpt text of at most the last 10 frames."""
    lines: list[str] = []
    for f in frames[-10:]:
        raw_fn = f.get("filename") or f.get("abs_path") or "unknown"
        norm_fn = _normalize_frame_path(str(raw_fn), path_prefix_strip)
        lineno = f.get("lineno", "?")
        func = f.get("function") or "<unknown>"
        lib_marker = " [lib]" if _is_library_frame(f) else ""
        lines.append(f"{norm_fn}:{lineno} in {func}{lib_marker}")

        ctx = f.get("context_line")
        if ctx and isinstance(ctx, str) and ctx.strip():
            lines.append(f"    {ctx.strip()}")

    lines.append(f"{exc_type}: {exc_value}")
    return "\n".join(lines)


def parse_sentry(payload: dict, *, path_prefix_strip: str | None = None) -> Incident:
    """Turn a Sentry error payload into an Incident model. Pure, deterministic, no side effects."""
    if not isinstance(payload, dict):
        raise ParseError("payload must be a dictionary")

    if path_prefix_strip is None:
        from ichnoscope.config import get_settings

        path_prefix_strip = get_settings().path_prefix_strip

    event = _find_event(payload)

    # Incident ID
    raw_id = event.get("event_id") or event.get("eventID")
    if not raw_id or not isinstance(raw_id, str) or not raw_id.strip():
        raise ParseError("missing event_id in event")
    incident_id = raw_id.strip()

    # Exception values
    exc_obj = event.get("exception")
    if not isinstance(exc_obj, dict):
        raise ParseError("missing exception object in event")
    values = exc_obj.get("values")
    if not isinstance(values, list) or not values:
        raise ParseError("exception values list is empty or missing")

    # Pick propagating (last) exception
    last_exc = values[-1]
    if not isinstance(last_exc, dict):
        raise ParseError("invalid exception value entry")
    exc_type = last_exc.get("type")
    if not exc_type or not isinstance(exc_type, str) or not exc_type.strip():
        raise ParseError("missing exception type")
    exc_value = "" if last_exc.get("value") is None else str(last_exc.get("value"))

    # Stacktrace & frames
    stacktrace = last_exc.get("stacktrace")
    if not isinstance(stacktrace, dict):
        raise ParseError("missing stacktrace in exception")
    frames = stacktrace.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ParseError("no frames in stack trace")

    # Select failing application frame
    frame = _pick_failing_frame(frames)
    raw_filename = frame.get("filename") or frame.get("abs_path")
    if not raw_filename or not isinstance(raw_filename, str) or not raw_filename.strip():
        raise ParseError("chosen frame is missing filename")

    raw_lineno = frame.get("lineno")
    if raw_lineno is None:
        raise ParseError("chosen frame is missing lineno")
    try:
        line_number = int(raw_lineno)
    except (ValueError, TypeError) as err:
        raise ParseError(f"chosen frame has invalid lineno: {raw_lineno}") from err
    if line_number < 1:
        raise ParseError(f"chosen frame lineno must be >= 1, got {line_number}")

    # File path normalization
    file_path = _normalize_frame_path(raw_filename, path_prefix_strip)

    # Timestamp
    occurred_at = _parse_timestamp(event)

    # Release SHA
    release_sha = _parse_release_sha(event)

    # Environment
    env_val = event.get("environment")
    if not env_val:
        tags = event.get("tags")
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, (list, tuple)) and len(t) >= 2 and t[0] == "environment":
                    env_val = t[1]
                    break
                elif isinstance(t, dict) and t.get("key") == "environment":
                    env_val = t.get("value")
                    break
    environment = str(env_val).strip() if env_val else "production"

    # Event count & users affected
    ichnoscope_meta = payload.get("_ichnoscope") if isinstance(payload.get("_ichnoscope"), dict) else {}
    data_meta = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    issue_meta = data_meta.get("issue") if isinstance(data_meta.get("issue"), dict) else {}

    cnt = _parse_count_val(ichnoscope_meta.get("event_count"))
    if cnt is None:
        cnt = _parse_count_val(issue_meta.get("count"))
    if cnt is None:
        cnt = 1
    event_count = max(1, cnt)

    usr = _parse_count_val(ichnoscope_meta.get("users_affected"))
    if usr is None:
        usr = _parse_count_val(issue_meta.get("userCount"))
    if usr is None:
        usr = 0
    users_affected = max(0, usr)

    # Stack excerpt
    stack_excerpt = _build_stack_excerpt(frames, path_prefix_strip, exc_type, exc_value)

    return Incident(
        incident_id=incident_id,
        source="sentry",
        occurred_at=occurred_at,
        release_sha=release_sha,
        exception_type=exc_type,
        error_message=exc_value,
        file_path=file_path,
        line_number=line_number,
        stack_excerpt=stack_excerpt,
        environment=environment,
        event_count=event_count,
        users_affected=users_affected,
    )
