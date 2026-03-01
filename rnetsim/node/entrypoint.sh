#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# RNETSIM Node Entrypoint
#
# Reads environment variables, generates ~/.reticulum/config, starts health
# monitor in background, then execs rnsd as PID 1.
# ---------------------------------------------------------------------------

NODE_NAME="${RNETSIM_NODE_NAME:-node}"
NODE_ROLE="${RNETSIM_NODE_ROLE:-endpoint}"
INTERFACES="${RNETSIM_INTERFACES:-[]}"
LXMF_PROPAGATION="${RNETSIM_LXMF_PROPAGATION:-false}"

# Determine transport mode
ENABLE_TRANSPORT="False"
if [ "$NODE_ROLE" = "transport" ]; then
    ENABLE_TRANSPORT="True"
fi

# Create Reticulum config directory
mkdir -p ~/.reticulum

# ---------------------------------------------------------------------------
# Generate ~/.reticulum/config
# ---------------------------------------------------------------------------
cat > ~/.reticulum/config << RETICULUMEOF
[reticulum]
  enable_transport = ${ENABLE_TRANSPORT}
  share_instance = Yes

[logging]
  loglevel = 4

[interfaces]
  [[Default Interface]]
    type = TCPServerInterface
    listen_ip = 0.0.0.0
    listen_port = 4242

RETICULUMEOF

# Parse RNETSIM_INTERFACES JSON and append TCPClientInterface entries
# Format: [{"name": "link-to-X", "target_host": "X", "target_port": 4242}]
if [ "$INTERFACES" != "[]" ]; then
    python3 -c "
import json, sys

interfaces = json.loads('''${INTERFACES}''')
for iface in interfaces:
    name = iface.get('name', 'link')
    host = iface['target_host']
    port = iface.get('target_port', 4242)
    print(f'''  [[{name}]]
    type = TCPClientInterface
    target_host = {host}
    target_port = {port}
    connect_timeout = 10
    reconnect_delay = 5
''')
" >> ~/.reticulum/config
fi

echo "[entrypoint] Node: ${NODE_NAME} (${NODE_ROLE})"
echo "[entrypoint] Config generated:"
cat ~/.reticulum/config

# ---------------------------------------------------------------------------
# Start health endpoint in background
# ---------------------------------------------------------------------------
python3 /health.py --serve &

# ---------------------------------------------------------------------------
# Start LXMF propagation node if configured
# ---------------------------------------------------------------------------
if [ "$LXMF_PROPAGATION" = "true" ]; then
    python3 -c "
import RNS, LXMF, time, threading

def start_propagation():
    time.sleep(5)  # Wait for rnsd to initialize
    r = RNS.Reticulum()
    propagation = LXMF.LXMPropagationNode(r)
    while True:
        time.sleep(60)

t = threading.Thread(target=start_propagation, daemon=True)
t.start()
" &
fi

# ---------------------------------------------------------------------------
# Exec rnsd as PID 1
# ---------------------------------------------------------------------------
exec rnsd --service
