"""Minimal deployed-stack smoke test.

Run after ``docker compose up --build``. This deliberately checks only service
wiring; domain behavior is covered by the backend test suite.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def request(path: str, *, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read() or b"{}")
        raise RuntimeError(f"{method} {path} returned {error.code}: {payload}") from error


def main() -> int:
    status, health = request("/health")
    if status != 200 or health.get("status") != "ok":
        raise RuntimeError(f"Unhealthy API: {status} {health}")

    suffix = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    status, venue = request(
        "/v1/venues",
        method="POST",
        body={"name": f"Smoke venue {suffix}"},
    )
    if status not in {200, 201} or not venue.get("id"):
        raise RuntimeError("Venue creation did not return an id")

    print(f"Smoke test passed for {BASE_URL}; created {venue['id']}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Smoke test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
