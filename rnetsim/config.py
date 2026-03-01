"""Global configuration and path constants."""

from pathlib import Path
import os

# Base data directory — mounted as Docker volume in production
DATA_DIR = Path(os.environ.get("RNETSIM_DATA_DIR", "./data"))
SCENARIOS_DIR = DATA_DIR / "scenarios"
PROFILES_DIR = DATA_DIR / "profiles"
TERRAIN_CACHE_DIR = DATA_DIR / "terrain-cache"
LOGS_DIR = Path(".logs")

# Built-in scenarios bundled with the package
BUILTIN_SCENARIOS_DIR = Path(__file__).parent / "scenarios"

# Docker constants
NODE_IMAGE_NAME = "rnetsim-node"
NETWORK_PREFIX = "rnetsim-"

# Ports
VISUALIZER_PORT = 3000
NODE_RETICULUM_PORT = 4242
NODE_HEALTH_PORT = 8080
NODE_TELEMETRY_PORT = 9100

# WebSocket broadcast interval
WS_BROADCAST_INTERVAL = 1.0  # seconds

# PMTiles CDN (default online source)
PMTILES_CDN_URL = "https://build.protomaps.com/20240101.pmtiles"
