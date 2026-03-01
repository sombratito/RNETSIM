"""Launch a simulation scenario — create containers, network, and tc rules.

This is the primary orchestration capability. It reads a Scenario,
creates Docker infrastructure, and applies traffic shaping.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import docker

from rnetsim.config import NODE_IMAGE_NAME, NETWORK_PREFIX, NODE_RETICULUM_PORT
from rnetsim.fabric.events import EventScheduler
from rnetsim.fabric.link_model import get_profile
from rnetsim.fabric.state import SimulationState
from rnetsim.fabric.tc_shaper import apply_shaping
from rnetsim.gateway.bridge import get_gateway_port_mapping

if TYPE_CHECKING:
    from rnetsim.api.models.scenario import Scenario

logger = logging.getLogger(__name__)


def compute_link_topology(scenario: Scenario) -> dict[str, list[dict]]:
    """Compute which nodes connect to which.

    Default strategy: all nodes sharing the same medium type form a full mesh.
    Each entry tells a node which TCPClientInterface entries to create.

    Returns: {node_name: [{name, target_host, target_port}]}
    """
    topology: dict[str, list[dict]] = {node.name: [] for node in scenario.nodes}

    # Group nodes by medium
    medium_groups: dict[str, list[str]] = {}
    for node in scenario.nodes:
        for medium in node.interfaces:
            medium_groups.setdefault(medium, []).append(node.name)

    # Create full mesh within each medium group
    for medium, members in medium_groups.items():
        for i, node_name in enumerate(members):
            for j, peer_name in enumerate(members):
                if i < j:
                    # Each pair: lower-index node connects to higher-index as client
                    # Higher-index connects back via its own server (symmetric)
                    topology[node_name].append(
                        {
                            "name": f"link-to-{peer_name}",
                            "target_host": peer_name,
                            "target_port": NODE_RETICULUM_PORT,
                        }
                    )

    return topology


def build_env_vars(node, topology: dict[str, list[dict]]) -> dict[str, str]:
    """Build environment variables for a node container."""
    interfaces_json = json.dumps(topology.get(node.name, []))

    env = {
        "RNETSIM_NODE_NAME": node.name,
        "RNETSIM_NODE_ROLE": node.role,
        "RNETSIM_INTERFACES": interfaces_json,
    }

    if node.lat is not None:
        env["RNETSIM_LATITUDE"] = str(node.lat)
    if node.lon is not None:
        env["RNETSIM_LONGITUDE"] = str(node.lon)
    if node.alt is not None:
        env["RNETSIM_ALTITUDE"] = str(node.alt)
    if node.sleep_schedule:
        env["RNETSIM_SLEEP_SCHEDULE"] = node.sleep_schedule
    if node.lxmf_propagation:
        env["RNETSIM_LXMF_PROPAGATION"] = "true"

    return env


async def launch_scenario(scenario: Scenario, state: SimulationState) -> None:
    """Launch a complete simulation scenario.

    1. Create Docker network
    2. Compute link topology
    3. Create and start node containers
    4. Apply tc/netem shaping
    5. Start event scheduler
    """
    client = docker.from_env()
    network_name = f"{NETWORK_PREFIX}{scenario.name}"

    logger.info("Launching scenario: %s (%d nodes)", scenario.name, len(scenario.nodes))

    # Create Docker network
    network = client.networks.create(network_name, driver="bridge")
    state.network = network
    state.scenario = scenario
    logger.info("Created network: %s", network_name)

    # Compute topology
    topology = compute_link_topology(scenario)

    # Build gateway lookup: {node_name: host_port}
    gateway_map: dict[str, int] = {}
    for gw in (scenario.gateways or []):
        gateway_map[gw.node] = gw.host_port

    # Create and start containers
    for node in scenario.nodes:
        env = build_env_vars(node, topology)

        run_kwargs: dict = {
            "name": node.name,
            "environment": env,
            "network": network_name,
            "detach": True,
            "cap_add": ["NET_ADMIN"],
            "labels": {"rnetsim.scenario": scenario.name, "rnetsim.role": node.role},
        }

        # Expose gateway port to host if this node is a gateway
        if node.name in gateway_map:
            run_kwargs["ports"] = get_gateway_port_mapping(gateway_map[node.name])
            logger.info("Gateway %s: mapping port 4242 -> host:%d", node.name, gateway_map[node.name])

        container = client.containers.run(NODE_IMAGE_NAME, **run_kwargs)

        state.containers[node.name] = container
        logger.info("Started container: %s (%s)", node.name, node.role)

    # Apply tc/netem shaping to each container
    for node in scenario.nodes:
        container = state.containers[node.name]
        primary_medium = node.interfaces[0] if node.interfaces else "lora_sf8_125"
        profile = get_profile(primary_medium)
        apply_shaping(container, profile)
        logger.info("Applied %s shaping to %s", primary_medium, node.name)

    # Schedule events if any
    if scenario.events:
        from rnetsim.fabric.inject import execute_event

        scheduler = EventScheduler()
        state.event_scheduler = scheduler

        event_dicts = [e.model_dump() for e in scenario.events]
        await scheduler.schedule(
            event_dicts,
            lambda ev: execute_event(ev, state),
        )

    state.is_running = True
    logger.info("Scenario %s launched successfully", scenario.name)
