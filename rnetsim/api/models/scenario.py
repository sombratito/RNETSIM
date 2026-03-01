"""Pydantic models for scenario YAML files.

Validates scenario structure, rejects unknown mediums, duplicate names,
and port conflicts.
"""

from __future__ import annotations

from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from rnetsim.fabric.link_model import VALID_MEDIUMS


class ScenarioNode(BaseModel):
    """A single node in the simulation."""

    name: str
    role: str = "endpoint"
    profile: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None
    interfaces: list[str] = Field(default_factory=lambda: ["lora_sf8_125"])
    sleep_schedule: Optional[str] = None
    lxmf_propagation: bool = False

    @model_validator(mode="after")
    def validate_mediums(self) -> "ScenarioNode":
        for medium in self.interfaces:
            if medium not in VALID_MEDIUMS:
                valid = ", ".join(sorted(VALID_MEDIUMS))
                raise ValueError(f"Unknown medium '{medium}' on node '{self.name}'. Valid: {valid}")
        return self


class ScenarioEvent(BaseModel):
    """A scheduled event in the simulation timeline."""

    at: str  # Duration string: "5m", "2m30s", "10s"
    action: str  # kill_node, revive_node, partition, heal, add_node, change_link
    target: Optional[str] = None
    params: Optional[dict] = None


class ScenarioGateway(BaseModel):
    """A gateway exposing a node's Reticulum interface to the host."""

    node: str
    host_port: int = 4242


class ScenarioMap(BaseModel):
    """Map display configuration for the visualizer."""

    source: str = "protomaps"
    pmtiles_url: Optional[str] = None
    style: str = "dark"
    center: list[float] = Field(default_factory=lambda: [-78.6382, 35.7796])
    zoom: int = 12
    terrain: bool = False


class ScenarioDefaults(BaseModel):
    """Default values applied to nodes that don't specify their own."""

    medium: str = "lora_sf8_125"
    tx_power: int = 20
    role: str = "endpoint"


class Scenario(BaseModel):
    """Complete simulation scenario definition."""

    name: str
    description: str = ""
    featured: bool = False
    defaults: ScenarioDefaults = Field(default_factory=ScenarioDefaults)
    terrain: bool = False
    map: ScenarioMap = Field(default_factory=ScenarioMap)
    nodes: list[ScenarioNode]
    gateways: list[ScenarioGateway] = Field(default_factory=list)
    events: list[ScenarioEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_names(self) -> "Scenario":
        names = [n.name for n in self.nodes]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(f"Duplicate node names: {set(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_gateway_refs(self) -> "Scenario":
        node_names = {n.name for n in self.nodes}
        for gw in self.gateways:
            if gw.node not in node_names:
                raise ValueError(f"Gateway references unknown node '{gw.node}'")
        return self

    @model_validator(mode="after")
    def validate_gateway_ports(self) -> "Scenario":
        ports = [gw.host_port for gw in self.gateways]
        duplicates = [p for p in ports if ports.count(p) > 1]
        if duplicates:
            raise ValueError(f"Duplicate gateway ports: {set(duplicates)}")
        return self


def load_scenario_yaml(path: str) -> Scenario:
    """Load and validate a scenario from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return Scenario(**data)


def dump_scenario_yaml(scenario: Scenario) -> str:
    """Serialize a scenario to YAML string."""
    data = scenario.model_dump(exclude_none=True)
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
