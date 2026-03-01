"""Gateway bridge for external Reticulum app connectivity.

Gateway nodes expose their TCPServerInterface port to the host via Docker
port mapping. External apps (Sideband, NomadNet, MeshChat) connect using
a TCPClientInterface pointing to localhost:{mapped_port}.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_gateway_port_mapping(host_port: int) -> dict:
    """Build Docker port mapping for a gateway node.

    Returns a dict suitable for the `ports` argument in
    docker.containers.run(): {"4242/tcp": host_port}
    """
    return {"4242/tcp": host_port}


def generate_client_config(host_port: int, interface_name: str = "RNETSIM Gateway") -> str:
    """Generate Reticulum config snippet for external apps.

    Users copy this into their ~/.reticulum/config to connect
    their apps to the simulated network.
    """
    return (
        f"[[{interface_name}]]\n"
        f"  type = TCPClientInterface\n"
        f"  target_host = localhost\n"
        f"  target_port = {host_port}\n"
    )
