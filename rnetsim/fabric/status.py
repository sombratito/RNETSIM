"""Query status of a running simulation.

Polls node health endpoints and aggregates into a status snapshot.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from rnetsim.config import NODE_HEALTH_PORT
from rnetsim.fabric.state import SimulationState

logger = logging.getLogger(__name__)


def poll_node_health(container) -> dict[str, Any]:
    """Poll a single node's health endpoint via Docker exec."""
    try:
        exit_code, output = container.exec_run(
            ["python3", "-c", f"""
import urllib.request, json
try:
    r = urllib.request.urlopen('http://127.0.0.1:{NODE_HEALTH_PORT}/health', timeout=3)
    print(r.read().decode())
except Exception as e:
    print(json.dumps({{"status": "offline", "error": str(e)}}))
"""],
            timeout=5,
        )
        if exit_code == 0:
            return json.loads(output.decode().strip())
    except Exception as e:
        logger.debug("Health poll failed for %s: %s", container.name, e)

    return {"status": "offline", "node_name": container.name}


def get_status(state: SimulationState) -> dict[str, Any]:
    """Get aggregated status of all nodes in the simulation.

    Returns a dict suitable for JSON serialization and WebSocket broadcast.
    """
    if not state.is_running or not state.scenario:
        return {
            "running": False,
            "scenario_name": None,
            "nodes": [],
            "links": [],
        }

    nodes = []
    for name, container in state.containers.items():
        node_status = poll_node_health(container)

        # Find the scenario node definition for metadata
        scenario_node = next(
            (n for n in state.scenario.nodes if n.name == name), None
        )

        nodes.append({
            "name": name,
            "identity_hash": node_status.get("identity_hash", ""),
            "role": scenario_node.role if scenario_node else "endpoint",
            "status": node_status.get("status", "offline"),
            "lat": scenario_node.lat if scenario_node else None,
            "lon": scenario_node.lon if scenario_node else None,
            "path_count": node_status.get("path_count", 0),
            "announce_count": node_status.get("announce_count", 0),
            "link_count": node_status.get("link_count", 0),
            "uptime": node_status.get("uptime", 0),
        })

    # Build link state from topology
    links = []
    if state.scenario:
        for node in state.scenario.nodes:
            for medium in node.interfaces:
                for other in state.scenario.nodes:
                    if node.name < other.name and medium in other.interfaces:
                        links.append({
                            "source": node.name,
                            "target": other.name,
                            "medium": medium,
                        })

    return {
        "running": True,
        "scenario_name": state.scenario.name,
        "node_count": len(nodes),
        "nodes": nodes,
        "links": links,
    }
