"""Tests against an in-memory fake Concourse served through httpx.MockTransport."""

import copy
import json

import httpx
import pytest

from concourse_sync.__main__ import main
from concourse_sync.client import ConcourseError, connect, resolve_alert
from concourse_sync.crowding import check_crowding, clear_stale_gate_alerts
from concourse_sync.digest import build_shift_digest, sparkline

SEED = {
    "events": [
        {"id": "event-concourse-2026", "name": "Northstar Summit 2026", "city": "Atlanta",
         "date": "2026-09-27", "status": "live", "attendees": 120, "capacity": 240},
    ],
    "venues": [
        {"id": "venue-atrium", "name": "Atrium Stage", "capacity": 26, "occupancy": 24, "zone": "01 / MAIN HALL"},
        {"id": "venue-forum", "name": "The Forum", "capacity": 22, "occupancy": 9, "zone": "02 / EAST WING"},
        {"id": "venue-lab", "name": "Studio Lab", "capacity": 18, "occupancy": 18, "zone": "03 / UPPER LEVEL"},
        {"id": "venue-rooftop", "name": "Rooftop Garden", "capacity": 16, "occupancy": 3, "zone": "04 / OPEN AIR"},
    ],
    "alerts": [
        {"id": "alert-02", "title": "Microphone replacement needed in The Forum", "severity": "critical",
         "status": "open", "source": "stage-operations", "created_at": "2026-09-27T14:05:00Z"},
        {"id": "alert-03", "title": "Rooftop networking opens at 11:00 AM", "severity": "info",
         "status": "open", "source": "program-team", "created_at": "2026-09-27T14:10:00Z"},
        {"id": "alert-04", "title": "East entrance scanner is back online", "severity": "info",
         "status": "resolved", "source": "checkin-desk", "created_at": "2026-09-27T14:15:00Z"},
    ],
    "checkins": [
        {"id": "chk-0042", "ticket_id": "tkt-0042", "venue_id": "venue-rooftop",
         "attendee_name": "Quinn Ellis", "checked_in_at": "2026-09-27T14:49:00Z"},
    ],
}


class FakeConcourse:
    """Minimal stateful stand-in for the Concourse routes the worker uses."""

    def __init__(self):
        self.state = copy.deepcopy(SEED)
        self.calls: list[tuple[str, str]] = []

    def analytics(self) -> dict:
        open_count = sum(a["status"] == "open" for a in self.state["alerts"])
        return {
            "tickets_sold": 120, "checked_in": 42, "checkin_rate": 35.0, "revenue": 7300.0,
            "open_alerts": open_count,
            "venue_utilization": [{"name": v["name"], "occupancy": v["occupancy"], "capacity": v["capacity"]}
                                  for v in self.state["venues"]],
            "tickets_by_tier": [{"tier": "general", "count": 80}, {"tier": "vip", "count": 20},
                                {"tier": "student", "count": 20}],
            "checkins_by_hour": [{"hour": "2026-09-27T12:00:00Z", "count": 14},
                                 {"hour": "2026-09-27T13:00:00Z", "count": 15},
                                 {"hour": "2026-09-27T14:00:00Z", "count": 13}],
        }

    def __call__(self, request: httpx.Request) -> httpx.Response:
        method, path = request.method, request.url.path
        self.calls.append((method, path))
        if method == "GET" and path in ("/api/events", "/api/venues", "/api/alerts", "/api/checkins"):
            return httpx.Response(200, json=self.state[path.removeprefix("/api/")])
        if path == "/api/analytics" and method == "GET" or path == "/api/analytics/refresh" and method == "POST":
            return httpx.Response(200, json=self.analytics())
        if method == "POST" and path == "/api/alerts":
            body = json.loads(request.content)
            alert = {"id": f"alert-{len(self.state['alerts']) + 10:02d}", "status": "open",
                     "created_at": "2026-09-27T15:00:00Z", **body}
            self.state["alerts"].insert(0, alert)
            return httpx.Response(201, json=alert)
        if method == "PATCH" and path.startswith("/api/alerts/"):
            alert_id = path.rsplit("/", 1)[1]
            for alert in self.state["alerts"]:
                if alert["id"] == alert_id:
                    alert.update(json.loads(request.content))
                    return httpx.Response(200, json=alert)
            return httpx.Response(404, json={"detail": "Alert not found"})
        return httpx.Response(404, json={"detail": "Not Found"})

    def venue(self, name: str) -> dict:
        return next(v for v in self.state["venues"] if v["name"] == name)


@pytest.fixture
def fake():
    return FakeConcourse()


@pytest.fixture
def client(fake):
    with connect("http://concourse.test", transport=httpx.MockTransport(fake)) as client:
        yield client


def test_digest_summarizes_the_shift(client):
    text = build_shift_digest(client)
    assert text.startswith("# Shift digest: Northstar Summit 2026")
    assert "- Tickets sold: 120" in text
    assert "- Checked in: 42" in text
    assert "- Check-in rate: 35.0%" in text
    assert "- Revenue: $7,300.00" in text
    assert "Last check-in: Quinn Ellis" in text
    busiest = text.split("## Busiest venues")[1].split("##")[0]
    assert busiest.index("Studio Lab") < busiest.index("Atrium Stage") < busiest.index("The Forum")
    assert "Rooftop Garden" not in busiest
    assert "## Open alerts (2)" in text
    assert "- critical: 1" in text and "- warning: 0" in text and "- info: 1" in text
    assert "East entrance scanner" not in text
    assert f"`{sparkline([14, 15, 13])}` 12:00–14:00 UTC · peak 15/h" in text


def test_sparkline_scales_to_peak():
    assert sparkline([0, 5, 10]) == "▁▅█"
    assert sparkline([]) == ""


def test_crowding_raises_once_and_dedupes(client, fake):
    raised = check_crowding(client, threshold=0.9)
    assert [(a["title"], a["severity"], a["source"]) for a in raised] == [
        ("Gate sync: Atrium Stage at 92%", "warning", "gate-sync"),
        ("Gate sync: Studio Lab at 100%", "critical", "gate-sync"),
    ]
    assert ("POST", "/api/analytics/refresh") in fake.calls

    assert check_crowding(client, threshold=0.9) == []
    fake.venue("Atrium Stage")["occupancy"] = 25  # 96%: same venue, new title, still covered
    assert check_crowding(client, threshold=0.9) == []
    gate_alerts = [a for a in fake.state["alerts"] if a["source"] == "gate-sync"]
    assert len(gate_alerts) == 2


def test_clear_resolves_only_venues_back_under_threshold(client, fake):
    check_crowding(client, threshold=0.9)
    fake.venue("Atrium Stage")["occupancy"] = 12
    resolved = clear_stale_gate_alerts(client, threshold=0.9)
    assert [a["title"] for a in resolved] == ["Gate sync: Atrium Stage at 92%"]
    assert ("PATCH", f"/api/alerts/{resolved[0]['id']}") in fake.calls
    statuses = {a["title"]: a["status"] for a in fake.state["alerts"]}
    assert statuses["Gate sync: Atrium Stage at 92%"] == "resolved"
    assert statuses["Gate sync: Studio Lab at 100%"] == "open"
    assert statuses["Microphone replacement needed in The Forum"] == "open"
    assert clear_stale_gate_alerts(client, threshold=0.9) == []


def test_non_2xx_raises_readable_detail(client):
    with pytest.raises(ConcourseError) as error:
        resolve_alert(client, "alert-missing")
    assert error.value.status_code == 404
    assert error.value.detail == "Alert not found"
    assert str(error.value) == "Concourse PATCH /api/alerts/alert-missing failed (404): Alert not found"


def test_cli_reports_unreachable_concourse(capsys):
    assert main(["--url", "http://127.0.0.1:9", "digest"]) == 2
    assert "Could not reach Concourse" in capsys.readouterr().err
