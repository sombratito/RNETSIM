"""API integration tests for scenario endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestScenarioAPI:
    def test_list_scenarios(self, api_client: TestClient):
        resp = api_client.get("/api/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Should have built-in scenarios
        assert len(data) >= 8

    def test_list_includes_minimal(self, api_client: TestClient):
        resp = api_client.get("/api/scenarios")
        names = [s["name"] for s in resp.json()]
        assert "minimal" in names

    def test_get_scenario(self, api_client: TestClient):
        resp = api_client.get("/api/scenarios/minimal")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "minimal"
        assert len(data["nodes"]) > 0

    def test_get_nonexistent_returns_404(self, api_client: TestClient):
        resp = api_client.get("/api/scenarios/nonexistent-scenario-xyz")
        assert resp.status_code == 404

    def test_get_yaml(self, api_client: TestClient):
        resp = api_client.get("/api/scenarios/minimal/yaml")
        assert resp.status_code == 200
        text = resp.text
        assert "minimal" in text
        assert "nodes" in text

    def test_create_scenario(self, api_client: TestClient):
        scenario_data = {
            "name": "api-test-create",
            "description": "Created via API test",
            "nodes": [
                {"name": "n1", "role": "endpoint", "interfaces": ["lora_sf8_125"]},
                {"name": "n2", "role": "endpoint", "interfaces": ["lora_sf8_125"]},
            ],
        }
        resp = api_client.post("/api/scenarios", json=scenario_data)
        assert resp.status_code in (200, 201)

        # Verify it was saved
        resp2 = api_client.get("/api/scenarios/api-test-create")
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "api-test-create"

    def test_delete_scenario(self, api_client: TestClient):
        # Create first
        scenario_data = {
            "name": "api-test-delete",
            "nodes": [{"name": "n1"}],
        }
        api_client.post("/api/scenarios", json=scenario_data)

        # Delete
        resp = api_client.delete("/api/scenarios/api-test-delete")
        assert resp.status_code == 200

        # Verify gone
        resp2 = api_client.get("/api/scenarios/api-test-delete")
        assert resp2.status_code == 404
