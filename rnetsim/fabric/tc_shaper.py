"""tc/netem command generation and application.

Applies Linux traffic control rules inside node containers via docker exec.
Requires NET_ADMIN capability on the container.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rnetsim.fabric.link_model import LinkProfile

if TYPE_CHECKING:
    import docker

logger = logging.getLogger(__name__)

# Minimum burst for tbf — one MTU ensures low-bandwidth profiles work
MIN_BURST_BYTES = 1540


def generate_tc_commands(interface: str, profile: LinkProfile) -> list[str]:
    """Generate tc commands to shape traffic on an interface.

    Uses a two-qdisc stack:
      1. netem for latency/jitter/loss
      2. tbf for bandwidth limiting

    Returns a list of shell commands to execute in order.
    """
    commands = []

    # Clear any existing qdiscs (ignore errors if none exist)
    commands.append(f"tc qdisc del dev {interface} root 2>/dev/null || true")

    # netem: delay + jitter + loss
    netem_parts = [f"tc qdisc add dev {interface} root handle 1: netem"]
    netem_parts.append(f"delay {profile.latency} {profile.jitter}")
    if profile.loss != "0%":
        netem_parts.append(f"loss {profile.loss}")
    commands.append(" ".join(netem_parts))

    # tbf: bandwidth limiting (child of netem)
    # latency param = max time a packet can sit in the queue
    commands.append(
        f"tc qdisc add dev {interface} parent 1: handle 2: tbf"
        f" rate {profile.bandwidth} burst {MIN_BURST_BYTES} latency 400ms"
    )

    return commands


def apply_shaping(
    container: docker.models.containers.Container,
    profile: LinkProfile,
    interface: str = "eth0",
) -> None:
    """Apply tc/netem shaping inside a running container."""
    commands = generate_tc_commands(interface, profile)
    for cmd in commands:
        exit_code, output = container.exec_run(["sh", "-c", cmd])
        if exit_code != 0 and "del" not in cmd:
            logger.warning(
                "tc command failed in %s: %s -> %s",
                container.name,
                cmd,
                output.decode().strip(),
            )


def remove_shaping(
    container: docker.models.containers.Container,
    interface: str = "eth0",
) -> None:
    """Remove all tc qdiscs from a container interface."""
    container.exec_run(["sh", "-c", f"tc qdisc del dev {interface} root 2>/dev/null || true"])


def update_shaping(
    container: docker.models.containers.Container,
    profile: LinkProfile,
    interface: str = "eth0",
) -> None:
    """Replace tc rules with a new profile."""
    remove_shaping(container, interface)
    apply_shaping(container, profile, interface)
