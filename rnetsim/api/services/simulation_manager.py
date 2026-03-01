"""Simulation lifecycle management.

Wraps fabric capabilities with mutex (one sim at a time) and
provides the interface used by API routes.
"""

from __future__ import annotations

import asyncio
import logging

from rnetsim.api.models.scenario import Scenario
from rnetsim.fabric.inject import execute_event
from rnetsim.fabric.launch import launch_scenario
from rnetsim.fabric.state import SimulationState
from rnetsim.fabric.status import get_status
from rnetsim.fabric.stop import stop_scenario

logger = logging.getLogger(__name__)


class SimulationManager:
    """Manages the lifecycle of a single simulation.

    Only one simulation can run at a time. All operations are mutex-protected.
    """

    def __init__(self) -> None:
        self.state = SimulationState()
        self._lock = asyncio.Lock()

    async def launch(self, scenario: Scenario) -> dict:
        """Launch a scenario. Fails if one is already running."""
        async with self._lock:
            if self.state.is_running:
                raise RuntimeError(
                    f"Simulation '{self.state.scenario.name}' is already running. "
                    "Stop it first with POST /api/simulation/stop"
                )

            await launch_scenario(scenario, self.state)
            return {"status": "launched", "scenario": scenario.name}

    async def stop(self) -> dict:
        """Stop the running simulation."""
        async with self._lock:
            if not self.state.is_running:
                return {"status": "not_running"}

            name = self.state.scenario.name if self.state.scenario else "unknown"
            await stop_scenario(self.state)
            return {"status": "stopped", "scenario": name}

    def get_status(self) -> dict:
        """Get current simulation status snapshot."""
        return get_status(self.state)

    async def inject(self, event: dict) -> dict:
        """Inject a runtime event."""
        if not self.state.is_running:
            raise RuntimeError("No simulation running")

        await execute_event(event, self.state)
        return {"status": "injected", "event": event}
