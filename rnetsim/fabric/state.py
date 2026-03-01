"""Simulation state — shared mutable state for a running simulation.

Holds references to Docker containers, network, scenario, and event scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import docker.models.containers
    import docker.models.networks

    from rnetsim.api.models.scenario import Scenario
    from rnetsim.fabric.events import EventScheduler


@dataclass
class SimulationState:
    """Mutable state for a running simulation."""

    scenario: Optional[Scenario] = None
    containers: dict[str, docker.models.containers.Container] = field(default_factory=dict)
    network: Optional[docker.models.networks.Network] = None
    event_scheduler: Optional[EventScheduler] = None
    is_running: bool = False

    def reset(self) -> None:
        """Clear all state after teardown."""
        self.scenario = None
        self.containers.clear()
        self.network = None
        self.event_scheduler = None
        self.is_running = False
