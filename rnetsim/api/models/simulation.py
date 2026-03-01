"""Pydantic models for simulation state and status responses."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class NodeStatus(BaseModel):
    """Status of a single simulation node."""

    name: str
    identity_hash: str = ""
    role: str = "endpoint"
    status: str = "offline"  # healthy, degraded, offline, sleeping
    lat: Optional[float] = None
    lon: Optional[float] = None
    path_count: int = 0
    announce_count: int = 0
    link_count: int = 0
    uptime: float = 0


class LinkStatus(BaseModel):
    """Status of a link between two nodes."""

    source: str
    target: str
    medium: str


class SimulationStatus(BaseModel):
    """Aggregated status of the running simulation."""

    running: bool = False
    scenario_name: Optional[str] = None
    node_count: int = 0
    nodes: list[NodeStatus] = []
    links: list[LinkStatus] = []
