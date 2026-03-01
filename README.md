# Reticulum Network Simulator

Docker-based simulation of heterogeneous Reticulum mesh networks
with real-time visualization, bandwidth shaping, and geographic modeling.

## Why This Exists

The Reticulum community has no network simulator. Developers building on Reticulum currently test by running multiple instances on localhost with TCP interfaces, or by setting up physical hardware. There is no way to simulate 50 LoRa nodes spread across a mountain range, or to model what happens when a Transport Instance goes offline, or to stress-test announce propagation at scale, or to visualize mesh topology changes in real time.

**rnetsim** fills this gap. It provides a Docker Compose environment where each simulated node is a real Reticulum instance running in its own container, connected to other nodes through a network fabric that simulates physical layer characteristics: bandwidth limits, latency, packet loss, geographic distance, and radio propagation. Community apps like Sideband, MeshChat, and NomadNet can connect to simulated nodes and function exactly as they would on real hardware.

This project is open source (MIT license) and contributed to the Reticulum community by Kingsland Academy LLC.

## Dev Quickstart

**Prerequisites:** Python 3.11+, Node 18+, Docker

```bash
git clone https://github.com/kingsland/rnetsim.git
cd rnetsim
python dev.py. # or python3 dev.py
```

`dev.py` converges your environment step by step — creating the venv, installing deps, building the Docker image, and starting the dev servers. Say yes to each prompt, or re-run to skip what's already done. If you already have one or all of the prerequisites installed, it will just skip.

Once running, press `d` for the interactive dev menu:

| Key | Action                                     |
| --- | ------------------------------------------ |
| `d` | Dev menu (services, links, PIDs, commands) |
| `t` | Run pytest                                 |
| `o` | Open browser to web UI                     |
| `l` | Tail API log                               |
| `r` | Restart servers                            |
| `q` | Quit                                       |

**Services after convergence:**

| Service       | URL                                 |
| ------------- | ----------------------------------- |
| Web UI (Vite) | http://localhost:5173               |
| API           | http://localhost:3000/api/scenarios |
| WebSocket     | ws://localhost:3000/ws              |

**CLI usage** (from the project venv):

```bash
rnetsim doctor          # check environment
rnetsim up minimal      # launch a 3-node scenario
rnetsim status          # node status table
rnetsim inject kill alpha   # kill a node at runtime
rnetsim down            # stop simulation
```

**Tests:**

```bash
pytest tests/                  # unit + integration
cd web && npm run cy:open      # Cypress e2e (interactive)
cd web && npm run cy:run       # Cypress e2e (headless)
```
