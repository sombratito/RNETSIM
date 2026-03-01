"""Test fixtures for RNETSIM unit and integration tests.

Provides reusable fixtures for scenario creation, API testing,
and Docker-based integration tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rnetsim.api.models.scenario import Scenario, ScenarioNode


@pytest.fixture
def minimal_scenario() -> Scenario:
    """A minimal 3-node scenario for unit tests (no Docker required)."""
    return Scenario(
        name="test-minimal",
        description="Test scenario with 3 LoRa nodes",
        nodes=[
            ScenarioNode(name="alpha", role="transport", interfaces=["lora_sf8_125"]),
            ScenarioNode(name="bravo", role="endpoint", interfaces=["lora_sf8_125"]),
            ScenarioNode(name="charlie", role="endpoint", interfaces=["lora_sf8_125"]),
        ],
    )


@pytest.fixture
def geo_scenario() -> Scenario:
    """A scenario with geographic coordinates for terrain/RF tests."""
    return Scenario(
        name="test-geo",
        description="Geographic scenario in NC mountains",
        terrain=True,
        nodes=[
            ScenarioNode(
                name="hilltop-1",
                role="transport",
                lat=35.6100,
                lon=-82.3300,
                alt=1200,
                interfaces=["lora_sf7_125"],
            ),
            ScenarioNode(
                name="valley-1",
                role="endpoint",
                lat=35.6000,
                lon=-82.3200,
                alt=600,
                interfaces=["lora_sf7_125"],
            ),
            ScenarioNode(
                name="hilltop-2",
                role="transport",
                lat=35.6200,
                lon=-82.3100,
                alt=1100,
                interfaces=["lora_sf7_125"],
            ),
        ],
    )


@pytest.fixture
def heterogeneous_scenario() -> Scenario:
    """A scenario with multiple medium types for topology tests."""
    return Scenario(
        name="test-hetero",
        description="Mixed media scenario",
        nodes=[
            ScenarioNode(name="lora-1", interfaces=["lora_sf8_125"]),
            ScenarioNode(name="lora-2", interfaces=["lora_sf8_125"]),
            ScenarioNode(name="wifi-1", interfaces=["wifi_local"]),
            ScenarioNode(name="wifi-2", interfaces=["wifi_local"]),
            ScenarioNode(name="bridge", interfaces=["lora_sf8_125", "wifi_local"]),
        ],
    )


@pytest.fixture
def gateway_scenario() -> Scenario:
    """A scenario with a gateway node."""
    from rnetsim.api.models.scenario import ScenarioGateway

    return Scenario(
        name="test-gateway",
        description="Gateway test scenario",
        nodes=[
            ScenarioNode(name="gw-node", role="transport", interfaces=["lora_sf8_125"]),
            ScenarioNode(name="endpoint-1", role="endpoint", interfaces=["lora_sf8_125"]),
        ],
        gateways=[ScenarioGateway(node="gw-node", host_port=14242)],
    )


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Temporary data directory for file-based store tests."""
    scenarios_dir = tmp_path / "scenarios"
    profiles_dir = tmp_path / "profiles"
    scenarios_dir.mkdir()
    profiles_dir.mkdir()
    return tmp_path


@pytest.fixture
def api_client() -> TestClient:
    """FastAPI test client for API integration tests."""
    from rnetsim.api.app import create_app

    app = create_app()
    return TestClient(app)
