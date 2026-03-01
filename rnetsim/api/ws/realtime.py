"""WebSocket real-time broadcast handler.

Polls node health at 1Hz, aggregates into state snapshot,
broadcasts to all connected WebSocket clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from rnetsim.api.services.simulation_manager import SimulationManager

logger = logging.getLogger(__name__)

# Connected WebSocket clients
_clients: set[WebSocket] = set()
_broadcast_task: asyncio.Task | None = None


async def websocket_handler(websocket: WebSocket, manager: SimulationManager) -> None:
    """Handle a WebSocket connection."""
    await websocket.accept()
    _clients.add(websocket)
    logger.info("WebSocket client connected (%d total)", len(_clients))

    try:
        while True:
            # Accept but ignore client messages (keep-alive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.discard(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(_clients))


async def start_broadcast_loop(manager: SimulationManager) -> None:
    """Start the background broadcast loop."""
    global _broadcast_task
    if _broadcast_task and not _broadcast_task.done():
        return

    _broadcast_task = asyncio.create_task(_broadcast_loop(manager))


async def _broadcast_loop(manager: SimulationManager) -> None:
    """Poll status and broadcast to all clients at 1Hz."""
    while True:
        if _clients:
            try:
                status = manager.get_status()
                message = json.dumps(status)

                disconnected = set()
                for client in _clients.copy():
                    try:
                        await client.send_text(message)
                    except Exception:
                        disconnected.add(client)

                _clients.difference_update(disconnected)
            except Exception as e:
                logger.error("Broadcast error: %s", e)

        await asyncio.sleep(1.0)
