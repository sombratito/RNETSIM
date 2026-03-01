"""Health check endpoint for RNETSIM node containers.

Runs as a background HTTP server on port 8080. Connects to the local
shared rnsd instance and reports node state.

Usage:
    python health.py --serve   # Start HTTP server (background)
    python health.py --check   # Exit 0 if healthy, 1 if not (Docker HEALTHCHECK)
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

HEALTH_PORT = 8080
NODE_NAME = os.environ.get("RNETSIM_NODE_NAME", "node")
START_TIME = time.time()


def get_node_status() -> dict:
    """Query the local Reticulum shared instance for status."""
    try:
        import RNS

        reticulum = RNS.Reticulum()

        identity_hash = ""
        if RNS.Transport.identity:
            identity_hash = RNS.hexrep(RNS.Transport.identity.hash, delimit=False)

        path_count = len(RNS.Transport.path_table) if hasattr(RNS.Transport, "path_table") else 0
        announce_count = (
            len(RNS.Transport.announce_table) if hasattr(RNS.Transport, "announce_table") else 0
        )
        link_count = (
            len(RNS.Transport.active_links) if hasattr(RNS.Transport, "active_links") else 0
        )

        return {
            "status": "healthy",
            "node_name": NODE_NAME,
            "identity_hash": identity_hash,
            "uptime": round(time.time() - START_TIME, 1),
            "path_count": path_count,
            "announce_count": announce_count,
            "link_count": link_count,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "node_name": NODE_NAME,
            "error": str(e),
            "uptime": round(time.time() - START_TIME, 1),
        }


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for /health endpoint."""

    def do_GET(self) -> None:
        if self.path == "/health":
            status = get_node_status()
            body = json.dumps(status).encode()
            self.send_response(200 if status["status"] == "healthy" else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.write(body)
        else:
            self.send_error(404)

    def write(self, body: bytes) -> None:
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass  # Suppress request logging


def main() -> None:
    if "--check" in sys.argv:
        try:
            import urllib.request

            req = urllib.request.urlopen(f"http://127.0.0.1:{HEALTH_PORT}/health", timeout=3)
            data = json.loads(req.read())
            sys.exit(0 if data.get("status") == "healthy" else 1)
        except Exception:
            sys.exit(1)

    elif "--serve" in sys.argv:
        server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
        print(f"[health] Listening on port {HEALTH_PORT}")
        server.serve_forever()

    else:
        print("Usage: health.py --serve | --check")
        sys.exit(1)


if __name__ == "__main__":
    main()
