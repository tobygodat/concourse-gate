"""Gate-side crowding watch: raise and clear venue capacity alerts in Concourse."""

import httpx

from concourse_sync.client import fetch_alerts, fetch_venues, raise_alert, refresh_analytics, resolve_alert
from concourse_sync.config import GATE_SOURCE

TITLE_PREFIX = "Gate sync: "


def crowding_title(venue_name: str, ratio: float) -> str:
    """Format the alert title for a crowded venue, e.g. 'Gate sync: Atrium Stage at 92%'."""
    return f"{TITLE_PREFIX}{venue_name} at {round(ratio * 100)}%"


def venue_from_title(title: str) -> str | None:
    """Recover the venue name from a gate-sync alert title, or None for other alerts."""
    if not title.startswith(TITLE_PREFIX) or " at " not in title:
        return None
    return title[len(TITLE_PREFIX):].rsplit(" at ", 1)[0]


def occupancy_ratio(venue: dict) -> float:
    """Return occupancy as a 0..1+ fraction of capacity (0 for zero-capacity venues)."""
    return venue["occupancy"] / venue["capacity"] if venue["capacity"] else 0.0


def open_gate_alerts(client: httpx.Client) -> list[dict]:
    """List open alerts that this worker raised."""
    return [a for a in fetch_alerts(client) if a["status"] == "open" and a["source"] == GATE_SOURCE]


def check_crowding(client: httpx.Client, threshold: float = 0.9) -> list[dict]:
    """Refresh analytics, then raise one alert per venue at or above threshold; return alerts raised.

    Severity is critical when a venue is full, warning otherwise. A venue is skipped when
    an open alert already has the same title, or any open gate-sync alert already covers
    that venue (so a 92% -> 96% change does not stack a second alert).
    """
    refresh_analytics(client)
    open_alerts = [a for a in fetch_alerts(client) if a["status"] == "open"]
    open_titles = {a["title"] for a in open_alerts}
    covered_venues = {venue_from_title(a["title"]) for a in open_alerts if a["source"] == GATE_SOURCE}

    raised = []
    for venue in fetch_venues(client):
        ratio = occupancy_ratio(venue)
        if ratio < threshold:
            continue
        title = crowding_title(venue["name"], ratio)
        if title in open_titles or venue["name"] in covered_venues:
            continue
        severity = "critical" if ratio >= 1.0 else "warning"
        raised.append(raise_alert(client, title, severity))
        open_titles.add(title)
    return raised


def clear_stale_gate_alerts(client: httpx.Client, threshold: float = 0.9) -> list[dict]:
    """Resolve open gate-sync alerts whose venue is now under threshold; return alerts resolved."""
    ratios = {venue["name"]: occupancy_ratio(venue) for venue in fetch_venues(client)}
    resolved = []
    for alert in open_gate_alerts(client):
        venue_name = venue_from_title(alert["title"])
        if venue_name is None or ratios.get(venue_name, 0.0) >= threshold:
            continue
        resolved.append(resolve_alert(client, alert["id"]))
    return resolved
