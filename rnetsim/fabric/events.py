"""Scheduled event engine for runtime simulation events.

Parses duration strings, schedules events with asyncio,
and executes actions against running containers.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from rnetsim.fabric.state import SimulationState

logger = logging.getLogger(__name__)


def parse_duration(duration_str: str) -> float:
    """Parse a duration string like '5m', '2m30s', '10s', '1h' to seconds."""
    total = 0.0
    pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(h|m|s)", re.IGNORECASE)
    matches = pattern.findall(duration_str)

    if not matches:
        raise ValueError(f"Invalid duration format: '{duration_str}'. Use e.g. '5m', '2m30s', '10s'")

    for value, unit in matches:
        multiplier = {"h": 3600, "m": 60, "s": 1}[unit.lower()]
        total += float(value) * multiplier

    return total


class EventScheduler:
    """Schedules and executes simulation events based on timeline definitions."""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def schedule(
        self,
        events: list[dict],
        execute_fn: Callable[[dict], Awaitable[None]],
    ) -> None:
        """Schedule all events from a scenario definition.

        Args:
            events: List of event dicts with 'at', 'action', 'target', 'params'.
            execute_fn: Async function to execute each event.
        """
        self._running = True

        for event in events:
            delay = parse_duration(event["at"])
            task = asyncio.create_task(self._delayed_execute(delay, event, execute_fn))
            self._tasks.append(task)

        logger.info("Scheduled %d events", len(events))

    async def _delayed_execute(
        self,
        delay: float,
        event: dict,
        execute_fn: Callable[[dict], Awaitable[None]],
    ) -> None:
        """Wait for delay then execute the event."""
        try:
            await asyncio.sleep(delay)
            if self._running:
                logger.info("Executing event: %s at T+%.0fs", event["action"], delay)
                await execute_fn(event)
        except asyncio.CancelledError:
            pass

    def cancel_all(self) -> None:
        """Cancel all scheduled events."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("All scheduled events cancelled")
