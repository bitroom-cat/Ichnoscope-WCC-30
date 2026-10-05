"""Rule-based incident severity classifier rating incidents as P1-Critical, P2-High, or P3-Medium.

Severity is determined deterministically from telemetry numbers; the LLM never assigns severity.
A threshold value of 0 disables that specific evaluation rule.
"""

from typing import TYPE_CHECKING

from ichnoscope.models import Incident, Severity

if TYPE_CHECKING:
    from ichnoscope.config import Settings


def rate_with_reason(incident: Incident, settings: "Settings | None" = None) -> tuple[Severity, str]:
    """Calculate the incident severity level and human-readable justification.

    Rules:
    - Only production environments ('production' or 'prod', case-insensitive trimmed) qualify for P1 or P2.
    - Evaluation priority: P1-Critical -> P2-High -> P3-Medium.
    - If a threshold is set to 0, that individual threshold check is disabled.
    - If both users and events satisfy a severity level, the users rule is mentioned first in the reason.
    """
    if settings is None:
        from ichnoscope.config import get_settings

        settings = get_settings()

    env_norm = incident.environment.strip().lower()
    if env_norm not in {"production", "prod"}:
        return "P3-Medium", f"P3: not a production environment ({incident.environment})"

    u = incident.users_affected
    e = incident.event_count

    # P1 check (threshold > 0 enables rule)
    p1_u_match = settings.p1_users > 0 and u >= settings.p1_users
    p1_e_match = settings.p1_events > 0 and e >= settings.p1_events

    if p1_u_match and p1_e_match:
        return "P1-Critical", f"P1: {u} users affected >= {settings.p1_users} and {e} events >= {settings.p1_events} in production"
    if p1_u_match:
        return "P1-Critical", f"P1: {u} users affected >= {settings.p1_users} in production"
    if p1_e_match:
        return "P1-Critical", f"P1: {e} events >= {settings.p1_events} in production"

    # P2 check (threshold > 0 enables rule)
    p2_u_match = settings.p2_users > 0 and u >= settings.p2_users
    p2_e_match = settings.p2_events > 0 and e >= settings.p2_events

    if p2_u_match and p2_e_match:
        return "P2-High", f"P2: {u} users affected >= {settings.p2_users} and {e} events >= {settings.p2_events} in production"
    if p2_u_match:
        return "P2-High", f"P2: {u} users affected >= {settings.p2_users} in production"
    if p2_e_match:
        return "P2-High", f"P2: {e} events >= {settings.p2_events} in production"

    # P3 fallback
    return "P3-Medium", f"P3: below thresholds ({u} users, {e} events)"


def rate(incident: Incident, settings: "Settings | None" = None) -> Severity:
    """Classify incident severity as P1-Critical, P2-High, or P3-Medium."""
    return rate_with_reason(incident, settings)[0]
