"""Tests for scenario Pydantic models and YAML serialization."""

import tempfile
from pathlib import Path

import pytest

from rnetsim.api.models.scenario import (
    Scenario,
    ScenarioDefaults,
    ScenarioEvent,
    ScenarioGateway,
    ScenarioMap,
    ScenarioNode,
    dump_scenario_yaml,
    load_scenario_yaml,
)


class TestScenarioNode:
    def test_default_values(self):
        node = ScenarioNode(name="test-node")
        assert node.role == "endpoint"
        assert node.interfaces == ["lora_sf8_125"]
        assert node.lat is None
        assert node.lxmf_propagation is False

    def test_valid_medium(self):
        node = ScenarioNode(name="n1", interfaces=["wifi_local"])
        assert node.interfaces == ["wifi_local"]

    def test_invalid_medium_raises(self):
        with pytest.raises(ValueError, match="Unknown medium"):
            ScenarioNode(name="n1", interfaces=["not_a_real_medium"])

    def test_multiple_interfaces(self):
        node = ScenarioNode(name="bridge", interfaces=["lora_sf8_125", "wifi_local"])
        assert len(node.interfaces) == 2

    def test_geographic_fields(self):
        node = ScenarioNode(name="geo", lat=35.5, lon=-78.6, alt=200)
        assert node.lat == 35.5
        assert node.alt == 200


class TestScenario:
    def test_minimal_scenario(self, minimal_scenario: Scenario):
        assert minimal_scenario.name == "test-minimal"
        assert len(minimal_scenario.nodes) == 3

    def test_duplicate_names_rejected(self):
        with pytest.raises(ValueError, match="Duplicate node names"):
            Scenario(
                name="dup",
                nodes=[
                    ScenarioNode(name="alpha"),
                    ScenarioNode(name="alpha"),
                ],
            )

    def test_gateway_references_unknown_node(self):
        with pytest.raises(ValueError, match="unknown node"):
            Scenario(
                name="bad-gw",
                nodes=[ScenarioNode(name="alpha")],
                gateways=[ScenarioGateway(node="nonexistent", host_port=4242)],
            )

    def test_duplicate_gateway_ports(self):
        with pytest.raises(ValueError, match="Duplicate gateway ports"):
            Scenario(
                name="dup-ports",
                nodes=[
                    ScenarioNode(name="gw1"),
                    ScenarioNode(name="gw2"),
                ],
                gateways=[
                    ScenarioGateway(node="gw1", host_port=4242),
                    ScenarioGateway(node="gw2", host_port=4242),
                ],
            )

    def test_defaults(self):
        s = Scenario(name="defaults-test", nodes=[ScenarioNode(name="n1")])
        assert s.defaults.medium == "lora_sf8_125"
        assert s.terrain is False
        assert s.events == []
        assert s.gateways == []


class TestScenarioYaml:
    def test_round_trip(self, minimal_scenario: Scenario):
        yaml_str = dump_scenario_yaml(minimal_scenario)
        assert "test-minimal" in yaml_str
        assert "alpha" in yaml_str

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_str)
            f.flush()
            loaded = load_scenario_yaml(f.name)

        assert loaded.name == minimal_scenario.name
        assert len(loaded.nodes) == len(minimal_scenario.nodes)

    def test_events_round_trip(self):
        scenario = Scenario(
            name="events-test",
            nodes=[
                ScenarioNode(name="n1"),
                ScenarioNode(name="n2"),
            ],
            events=[
                ScenarioEvent(at="5m", action="kill_node", target="n1"),
                ScenarioEvent(at="10m", action="revive_node", target="n1"),
            ],
        )
        yaml_str = dump_scenario_yaml(scenario)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_str)
            f.flush()
            loaded = load_scenario_yaml(f.name)

        assert len(loaded.events) == 2
        assert loaded.events[0].action == "kill_node"
        assert loaded.events[1].at == "10m"


class TestBuiltinScenarios:
    """Verify all bundled YAML scenarios parse without errors."""

    def test_all_builtin_scenarios_parse(self):
        from rnetsim.config import BUILTIN_SCENARIOS_DIR

        yaml_files = list(BUILTIN_SCENARIOS_DIR.glob("*.yaml"))
        assert len(yaml_files) >= 8, f"Expected at least 8 built-in scenarios, found {len(yaml_files)}"

        for yaml_file in yaml_files:
            scenario = load_scenario_yaml(str(yaml_file))
            assert scenario.name, f"Scenario in {yaml_file.name} has no name"
            assert len(scenario.nodes) > 0, f"Scenario {scenario.name} has no nodes"
