"""API integration tests for simulation endpoints.

Note: These tests don't actually start Docker containers.
They test the API surface and error handling.
"""

import pytest
from fastapi.testclient import TestClient


class TestSimulationAPI:
    def test_status_when_not_running(self, api_client: TestClient):
        resp = api_client.get("/api/simulation/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is False

    def test_stop_when_not_running(self, api_client: TestClient):
        resp = api_client.post("/api/simulation/stop")
        # Should succeed (idempotent) or return appropriate status
        assert resp.status_code in (200, 400)

    def test_launch_nonexistent_scenario(self, api_client: TestClient):
        resp = api_client.post(
            "/api/simulation/launch",
            json={"scenario": "nonexistent-scenario-xyz"},
        )
        assert resp.status_code in (404, 400, 500)

    def test_inject_when_not_running(self, api_client: TestClient):
        resp = api_client.post(
            "/api/simulation/inject",
            json={"action": "kill_node", "target": "some-node"},
        )
        # Should fail gracefully when no simulation running
        assert resp.status_code in (400, 409, 500)
