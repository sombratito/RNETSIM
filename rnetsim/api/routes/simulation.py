"""Simulation lifecycle routes — launch, stop, status, inject."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from rnetsim.api.services import scenario_store

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


class LaunchRequest(BaseModel):
    scenario: str


class InjectRequest(BaseModel):
    action: str
    target: str | None = None
    params: dict | None = None


@router.post("/launch")
async def launch(req: LaunchRequest, request: Request) -> dict:
    """Launch a simulation scenario."""
    scenario = scenario_store.get_scenario(req.scenario)
    if not scenario:
        raise HTTPException(404, f"Scenario '{req.scenario}' not found")

    manager = request.app.state.simulation_manager
    try:
        return await manager.launch(scenario)
    except RuntimeError as e:
        raise HTTPException(409, str(e))


@router.post("/stop")
async def stop(request: Request) -> dict:
    """Stop the running simulation."""
    manager = request.app.state.simulation_manager
    return await manager.stop()


@router.get("/status")
def status(request: Request) -> dict:
    """Get simulation status."""
    manager = request.app.state.simulation_manager
    return manager.get_status()


@router.post("/inject")
async def inject(req: InjectRequest, request: Request) -> dict:
    """Inject a runtime event."""
    manager = request.app.state.simulation_manager
    try:
        return await manager.inject(req.model_dump(exclude_none=True))
    except RuntimeError as e:
        raise HTTPException(409, str(e))
