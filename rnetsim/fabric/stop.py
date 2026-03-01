"""Stop a running simulation — teardown containers, network, events."""

from __future__ import annotations

import logging

from rnetsim.fabric.state import SimulationState

logger = logging.getLogger(__name__)


async def stop_scenario(state: SimulationState) -> None:
    """Stop all containers, remove network, cancel events.

    Safe to call even if partially started — skips missing resources.
    """
    # Cancel scheduled events
    if state.event_scheduler:
        state.event_scheduler.cancel_all()
        logger.info("Event scheduler cancelled")

    # Stop and remove containers
    for name, container in state.containers.items():
        try:
            container.stop(timeout=5)
            container.remove(force=True)
            logger.info("Removed container: %s", name)
        except Exception as e:
            logger.warning("Failed to remove container %s: %s", name, e)

    # Remove network
    if state.network:
        try:
            state.network.remove()
            logger.info("Removed network: %s", state.network.name)
        except Exception as e:
            logger.warning("Failed to remove network: %s", e)

    state.reset()
    logger.info("Simulation stopped")
