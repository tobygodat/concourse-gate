"""Runtime settings for the Concourse Gate sync worker."""

import os

CONCOURSE_URL = os.environ.get("CONCOURSE_URL", "http://127.0.0.1:8010")
"""Base URL of the Concourse API; override with the CONCOURSE_URL environment variable."""

GATE_SOURCE = "gate-sync"
"""Alert source tag used for every alert this worker raises."""
