"""Explicit HTTP calls to the Concourse API, one named function per endpoint.

Every call site writes its full `/api/...` path literally so static indexers
(Fiada) can link each function to the Concourse route it hits.
"""

import httpx

from concourse_sync.config import CONCOURSE_URL, GATE_SOURCE


class ConcourseError(RuntimeError):
    """A non-2xx Concourse response, carrying FastAPI's readable `detail`."""

    def __init__(self, method: str, path: str, status_code: int, detail: str):
        self.method = method
        self.path = path
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Concourse {method} {path} failed ({status_code}): {detail}")


def connect(base_url: str = CONCOURSE_URL, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """Open an HTTP client pointed at the Concourse API (transport is injectable for tests)."""
    return httpx.Client(base_url=base_url, transport=transport, timeout=10.0)


def _checked(response: httpx.Response):
    """Return the JSON body, or raise ConcourseError using FastAPI's `{"detail": ...}` shape."""
    if response.is_success:
        return response.json()
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text or response.reason_phrase
    if not isinstance(detail, str):
        detail = "; ".join(item.get("msg", str(item)) if isinstance(item, dict) else str(item) for item in detail)
    request = response.request
    raise ConcourseError(request.method, request.url.path, response.status_code, detail)


def fetch_analytics(client: httpx.Client) -> dict:
    """Read the current analytics snapshot: sales, check-ins, revenue, utilization."""
    return _checked(client.get("/api/analytics"))


def fetch_alerts(client: httpx.Client) -> list[dict]:
    """List every operational alert, open and resolved."""
    return _checked(client.get("/api/alerts"))


def fetch_venues(client: httpx.Client) -> list[dict]:
    """List venues with their live occupancy and capacity."""
    return _checked(client.get("/api/venues"))


def fetch_checkins(client: httpx.Client) -> list[dict]:
    """List recorded attendee check-ins, newest first."""
    return _checked(client.get("/api/checkins"))


def fetch_events(client: httpx.Client) -> list[dict]:
    """List events with status and ticket counts."""
    return _checked(client.get("/api/events"))


def refresh_analytics(client: httpx.Client) -> dict:
    """Ask Concourse to rebuild its analytics snapshot and return the fresh numbers."""
    return _checked(client.post("/api/analytics/refresh"))


def raise_alert(client: httpx.Client, title: str, severity: str) -> dict:
    """Create an open alert tagged with the gate-sync source."""
    payload = {"title": title, "severity": severity, "source": GATE_SOURCE}
    return _checked(client.post("/api/alerts", json=payload))


def resolve_alert(client: httpx.Client, alert_id: str) -> dict:
    """Mark an existing alert as resolved."""
    return _checked(client.patch(f"/api/alerts/{alert_id}", json={"status": "resolved"}))
