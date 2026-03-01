"""FastAPI application factory.

Creates the unified API + SPA server. The REST layer is a thin adapter
over fabric capabilities (Principle 3). Static files serve the built
React app as an SPA.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rnetsim.api.routes import profiles, scenarios, simulation, terrain
from rnetsim.api.services.simulation_manager import SimulationManager
from rnetsim.api.ws.realtime import start_broadcast_loop, websocket_handler

# Static files directory for the built React app
STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize and teardown shared state."""
    manager = SimulationManager()
    app.state.simulation_manager = manager

    # Start WebSocket broadcast loop
    await start_broadcast_loop(manager)

    yield

    # Teardown: stop running simulation if any
    if manager.state.is_running:
        await manager.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RNETSIM",
        description="Reticulum Network Simulator API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS for Vite dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(scenarios.router)
    app.include_router(profiles.router)
    app.include_router(simulation.router)
    app.include_router(terrain.router)

    # WebSocket endpoint
    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        manager = app.state.simulation_manager
        await websocket_handler(websocket, manager)

    # Serve built React app as SPA (if dist exists)
    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            file_path = STATIC_DIR / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(STATIC_DIR / "index.html")
    else:
        @app.get("/")
        async def dev_root() -> dict:
            return {
                "message": "RNETSIM API running. Frontend not built yet.",
                "hint": "Run 'cd web && npm run build' or use Vite dev server on :5173",
            }

    return app
