"""Inject runtime events into a running simulation.

Event actions: kill_node, revive_node, partition, heal, add_node, change_link.
"""

from __future__ import annotations

import logging
from typing import Any

from rnetsim.fabric.state import SimulationState

logger = logging.getLogger(__name__)


async def execute_event(event: dict[str, Any], state: SimulationState) -> None:
    """Execute a single event against the running simulation.

    Args:
        event: Dict with 'action', 'target', and optional 'params'.
        state: Current simulation state.
    """
    action = event["action"]
    target = event.get("target")
    params = event.get("params", {})

    handler = EVENT_HANDLERS.get(action)
    if not handler:
        logger.error("Unknown event action: %s", action)
        return

    await handler(target, params, state)


async def handle_kill_node(
    target: str | None, params: dict, state: SimulationState
) -> None:
    """Stop a node container (simulates hardware failure)."""
    if not target or target not in state.containers:
        logger.warning("Kill target not found: %s", target)
        return

    container = state.containers[target]
    container.stop(timeout=2)
    logger.info("Killed node: %s", target)


async def handle_revive_node(
    target: str | None, params: dict, state: SimulationState
) -> None:
    """Restart a stopped node container."""
    if not target or target not in state.containers:
        logger.warning("Revive target not found: %s", target)
        return

    container = state.containers[target]
    container.start()
    logger.info("Revived node: %s", target)


async def handle_partition(
    target: str | None, params: dict, state: SimulationState
) -> None:
    """Partition network between two groups of nodes.

    Uses iptables inside containers to drop traffic between groups.
    Target format: "group_a" in params, "group_b" in params.
    """
    group_a = params.get("group_a", [])
    group_b = params.get("group_b", [])

    if not group_a or not group_b:
        logger.warning("Partition requires group_a and group_b params")
        return

    # For each node in group A, block traffic to all nodes in group B
    for node_a in group_a:
        container_a = state.containers.get(node_a)
        if not container_a:
            continue
        for node_b in group_b:
            container_b = state.containers.get(node_b)
            if not container_b:
                continue
            # Get container IP on the Docker network
            container_b.reload()
            networks = container_b.attrs.get("NetworkSettings", {}).get("Networks", {})
            for net_info in networks.values():
                ip = net_info.get("IPAddress")
                if ip:
                    container_a.exec_run(
                        ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"]
                    )
                    container_a.exec_run(
                        ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
                    )

    # Symmetric: block B -> A too
    for node_b in group_b:
        container_b = state.containers.get(node_b)
        if not container_b:
            continue
        for node_a in group_a:
            container_a = state.containers.get(node_a)
            if not container_a:
                continue
            container_a.reload()
            networks = container_a.attrs.get("NetworkSettings", {}).get("Networks", {})
            for net_info in networks.values():
                ip = net_info.get("IPAddress")
                if ip:
                    container_b.exec_run(
                        ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"]
                    )
                    container_b.exec_run(
                        ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
                    )

    logger.info("Partitioned: %s <-> %s", group_a, group_b)


async def handle_heal(
    target: str | None, params: dict, state: SimulationState
) -> None:
    """Heal all partitions by flushing iptables rules."""
    for name, container in state.containers.items():
        try:
            container.exec_run(["iptables", "-F"])
            logger.info("Flushed iptables for %s", name)
        except Exception as e:
            logger.warning("Failed to flush iptables for %s: %s", name, e)

    logger.info("All partitions healed")


EVENT_HANDLERS = {
    "kill_node": handle_kill_node,
    "revive_node": handle_revive_node,
    "partition": handle_partition,
    "heal": handle_heal,
}
