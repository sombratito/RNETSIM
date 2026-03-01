"""Filesystem CRUD for scenario YAML files.

Scans both built-in scenarios (bundled with package) and user scenarios
(in /data/scenarios/). Built-in scenarios are read-only.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from rnetsim.api.models.scenario import Scenario
from rnetsim.config import BUILTIN_SCENARIOS_DIR, SCENARIOS_DIR

logger = logging.getLogger(__name__)


def ensure_dirs() -> None:
    """Create scenario directories if they don't exist."""
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


def list_scenarios() -> list[dict]:
    """List all available scenarios (built-in + user)."""
    ensure_dirs()
    results = []

    for source_dir, is_builtin in [
        (BUILTIN_SCENARIOS_DIR, True),
        (SCENARIOS_DIR, False),
    ]:
        if not source_dir.exists():
            continue
        for path in sorted(source_dir.glob("*.yaml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                results.append({
                    "name": data.get("name", path.stem),
                    "description": data.get("description", ""),
                    "node_count": len(data.get("nodes", [])),
                    "built_in": is_builtin,
                    "featured": data.get("featured", False),
                    "path": str(path),
                })
            except Exception as e:
                logger.warning("Failed to read scenario %s: %s", path, e)

    # Featured scenarios first, then alphabetical
    results.sort(key=lambda s: (not s["featured"], s["name"]))
    return results


def get_scenario(name: str) -> Optional[Scenario]:
    """Load a scenario by name. Checks user dir first, then built-in."""
    ensure_dirs()

    for source_dir in [SCENARIOS_DIR, BUILTIN_SCENARIOS_DIR]:
        path = source_dir / f"{name}.yaml"
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
            return Scenario(**data)

    return None


def save_scenario(scenario: Scenario) -> Path:
    """Save a scenario to the user scenarios directory."""
    ensure_dirs()
    path = SCENARIOS_DIR / f"{scenario.name}.yaml"
    data = scenario.model_dump(exclude_none=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    logger.info("Saved scenario: %s", path)
    return path


def delete_scenario(name: str) -> bool:
    """Delete a user scenario. Rejects deletion of built-in scenarios."""
    builtin_path = BUILTIN_SCENARIOS_DIR / f"{name}.yaml"
    if builtin_path.exists():
        raise ValueError(f"Cannot delete built-in scenario '{name}'")

    user_path = SCENARIOS_DIR / f"{name}.yaml"
    if user_path.exists():
        user_path.unlink()
        logger.info("Deleted scenario: %s", name)
        return True
    return False


def duplicate_scenario(name: str) -> str:
    """Duplicate a scenario with '-copy' suffix."""
    scenario = get_scenario(name)
    if not scenario:
        raise ValueError(f"Scenario '{name}' not found")

    new_name = f"{name}-copy"
    counter = 1
    while (SCENARIOS_DIR / f"{new_name}.yaml").exists():
        new_name = f"{name}-copy-{counter}"
        counter += 1

    scenario.name = new_name
    save_scenario(scenario)
    return new_name


def get_scenario_yaml(name: str) -> Optional[str]:
    """Get raw YAML string for a scenario."""
    for source_dir in [SCENARIOS_DIR, BUILTIN_SCENARIOS_DIR]:
        path = source_dir / f"{name}.yaml"
        if path.exists():
            return path.read_text()
    return None
