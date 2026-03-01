"""Scenario CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile

from rnetsim.api.models.scenario import Scenario, dump_scenario_yaml
from rnetsim.api.services import scenario_store

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
def list_scenarios() -> list[dict]:
    """List all available scenarios."""
    return scenario_store.list_scenarios()


@router.get("/{name}")
def get_scenario(name: str) -> dict:
    """Get a scenario by name."""
    scenario = scenario_store.get_scenario(name)
    if not scenario:
        raise HTTPException(404, f"Scenario '{name}' not found")
    return scenario.model_dump(exclude_none=True)


@router.get("/{name}/yaml")
def get_scenario_yaml(name: str) -> Response:
    """Export scenario as raw YAML."""
    yaml_str = scenario_store.get_scenario_yaml(name)
    if not yaml_str:
        raise HTTPException(404, f"Scenario '{name}' not found")
    return Response(content=yaml_str, media_type="text/yaml")


@router.post("")
def create_scenario(scenario: Scenario) -> dict:
    """Create a new scenario."""
    existing = scenario_store.get_scenario(scenario.name)
    if existing:
        raise HTTPException(409, f"Scenario '{scenario.name}' already exists")
    scenario_store.save_scenario(scenario)
    return {"status": "created", "name": scenario.name}


@router.put("/{name}")
def update_scenario(name: str, scenario: Scenario) -> dict:
    """Update an existing scenario."""
    scenario.name = name
    scenario_store.save_scenario(scenario)
    return {"status": "updated", "name": name}


@router.delete("/{name}")
def delete_scenario(name: str) -> dict:
    """Delete a user scenario."""
    try:
        deleted = scenario_store.delete_scenario(name)
        if not deleted:
            raise HTTPException(404, f"Scenario '{name}' not found")
        return {"status": "deleted", "name": name}
    except ValueError as e:
        raise HTTPException(403, str(e))


@router.post("/{name}/duplicate")
def duplicate_scenario(name: str) -> dict:
    """Duplicate a scenario with '-copy' suffix."""
    try:
        new_name = scenario_store.duplicate_scenario(name)
        return {"status": "duplicated", "original": name, "new_name": new_name}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/import")
async def import_scenario(file: UploadFile) -> dict:
    """Import a scenario from an uploaded YAML file."""
    import yaml

    content = await file.read()
    try:
        data = yaml.safe_load(content.decode())
        scenario = Scenario(**data)
        scenario_store.save_scenario(scenario)
        return {"status": "imported", "name": scenario.name}
    except Exception as e:
        raise HTTPException(400, f"Invalid scenario YAML: {e}")
