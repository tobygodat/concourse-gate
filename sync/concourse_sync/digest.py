"""End-of-shift markdown digest assembled from Concourse read endpoints."""

from collections import Counter

import httpx

from concourse_sync.client import fetch_alerts, fetch_analytics, fetch_checkins, fetch_events, fetch_venues

SPARK_BARS = "▁▂▃▄▅▆▇█"
SEVERITY_ORDER = ("critical", "warning", "info")


def sparkline(counts: list[int]) -> str:
    """Render counts as a one-line text sparkline scaled to the largest value."""
    if not counts:
        return ""
    peak = max(counts) or 1
    return "".join(SPARK_BARS[round(count / peak * (len(SPARK_BARS) - 1))] for count in counts)


def pick_event(events: list[dict]) -> dict | None:
    """Choose the event to report on: the live one first, else the first listed."""
    for event in events:
        if event.get("status") == "live":
            return event
    return events[0] if events else None


def busiest_venues(venues: list[dict], limit: int = 3) -> list[dict]:
    """Rank venues by occupancy ratio, fullest first."""
    return sorted(venues, key=lambda v: v["occupancy"] / v["capacity"] if v["capacity"] else 0, reverse=True)[:limit]


def build_shift_digest(client: httpx.Client) -> str:
    """Build a markdown end-of-shift summary: attendance, revenue, venues, alerts, check-in curve."""
    event = pick_event(fetch_events(client))
    analytics = fetch_analytics(client)
    venues = fetch_venues(client)
    alerts = fetch_alerts(client)
    checkins = fetch_checkins(client)

    title = event["name"] if event else "Concourse"
    lines = [f"# Shift digest: {title}", ""]
    if event:
        lines.append(f"{event['city']} · {event['date']} · status **{event['status']}**")
        lines.append("")

    lines += [
        "## Attendance",
        f"- Tickets sold: {analytics['tickets_sold']}",
        f"- Checked in: {analytics['checked_in']}",
        f"- Check-in rate: {analytics['checkin_rate']:.1f}%",
        f"- Revenue: ${analytics['revenue']:,.2f}",
    ]
    if checkins:
        latest = checkins[0]
        lines.append(f"- Last check-in: {latest['attendee_name']} at {latest['checked_in_at']}")
    lines.append("")

    lines.append("## Busiest venues")
    for venue in busiest_venues(venues):
        pct = venue["occupancy"] / venue["capacity"] * 100 if venue["capacity"] else 0
        lines.append(f"- {venue['name']} ({venue['zone']}): {venue['occupancy']}/{venue['capacity']} · {pct:.0f}%")
    lines.append("")

    open_alerts = [alert for alert in alerts if alert["status"] == "open"]
    by_severity = Counter(alert["severity"] for alert in open_alerts)
    lines.append(f"## Open alerts ({len(open_alerts)})")
    for severity in SEVERITY_ORDER:
        lines.append(f"- {severity}: {by_severity.get(severity, 0)}")
    for alert in open_alerts:
        lines.append(f"  - [{alert['severity']}] {alert['title']} ({alert['source']})")
    lines.append("")

    hours = analytics.get("checkins_by_hour", [])
    lines.append("## Check-ins by hour")
    if hours:
        counts = [bucket["count"] for bucket in hours]
        first, last = hours[0]["hour"][11:16], hours[-1]["hour"][11:16]
        lines.append(f"`{sparkline(counts)}` {first}–{last} UTC · peak {max(counts)}/h")
        for bucket in hours:
            lines.append(f"- {bucket['hour'][11:16]}: {bucket['count']}")
    else:
        lines.append("No check-ins yet.")
    return "\n".join(lines) + "\n"
