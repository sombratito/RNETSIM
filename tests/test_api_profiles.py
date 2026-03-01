"""API integration tests for profile endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestProfileAPI:
    def test_list_profiles(self, api_client: TestClient):
        resp = api_client.get("/api/profiles")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 8  # 8 built-in profiles

    def test_builtin_profiles_present(self, api_client: TestClient):
        resp = api_client.get("/api/profiles")
        ids = [p["id"] for p in resp.json()]
        assert "edge-c2" in ids
        assert "field-node" in ids
        assert "hilltop-relay" in ids

    def test_get_profile(self, api_client: TestClient):
        resp = api_client.get("/api/profiles/edge-c2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "edge-c2"
        assert data["name"] == "Edge C2"
        assert data["built_in"] is True

    def test_get_nonexistent_returns_404(self, api_client: TestClient):
        resp = api_client.get("/api/profiles/nonexistent-profile")
        assert resp.status_code == 404

    def test_create_custom_profile(self, api_client: TestClient):
        profile_data = {
            "id": "test-custom",
            "name": "Test Custom",
            "abbreviation": "TC",
            "color": "#ff0000",
            "cpu": "2x A53",
            "ram": "1 GB",
            "radio": "LoRa SF8",
            "bandwidth_display": "3.1 kbps",
            "medium": "lora_sf8_125",
            "role": "endpoint",
            "built_in": False,
        }
        resp = api_client.post("/api/profiles", json=profile_data)
        assert resp.status_code in (200, 201)

    def test_cannot_delete_builtin(self, api_client: TestClient):
        resp = api_client.delete("/api/profiles/edge-c2")
        # Should either 400 or 403
        assert resp.status_code in (400, 403)
