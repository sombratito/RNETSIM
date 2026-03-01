"""Prometheus metrics exporter for RNETSIM node containers.

Serves Prometheus text format metrics on port 9100.
"""

import os
import resource
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEMETRY_PORT = 9100
NODE_NAME = os.environ.get("RNETSIM_NODE_NAME", "node")
START_TIME = time.time()


def collect_metrics() -> str:
    """Collect metrics from the local Reticulum instance."""
    lines = []

    try:
        import RNS

        RNS.Reticulum()

        path_count = len(RNS.Transport.path_table) if hasattr(RNS.Transport, "path_table") else 0
        announce_count = (
            len(RNS.Transport.announce_table) if hasattr(RNS.Transport, "announce_table") else 0
        )
        link_count = (
            len(RNS.Transport.active_links) if hasattr(RNS.Transport, "active_links") else 0
        )

        lines.append(f'rnetsim_paths_known{{node="{NODE_NAME}"}} {path_count}')
        lines.append(f'rnetsim_announces_known{{node="{NODE_NAME}"}} {announce_count}')
        lines.append(f'rnetsim_links_active{{node="{NODE_NAME}"}} {link_count}')
    except Exception:
        pass

    # Memory usage from resource module
    mem_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # KB to bytes on Linux
    lines.append(f'rnetsim_memory_usage_bytes{{node="{NODE_NAME}"}} {mem_bytes}')

    # Uptime
    lines.append(f'rnetsim_uptime_seconds{{node="{NODE_NAME}"}} {time.time() - START_TIME:.1f}')

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint."""

    def do_GET(self) -> None:
        if self.path == "/metrics":
            body = collect_metrics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    server = HTTPServer(("0.0.0.0", TELEMETRY_PORT), MetricsHandler)
    print(f"[telemetry] Listening on port {TELEMETRY_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
