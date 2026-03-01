# RNETSIM Architecture

This document orients developers, AI agents, and domain experts to the RNETSIM codebase. It covers what each layer does, how data flows, where to find things, and the design constraints that shaped the system.

## What RNETSIM Is

A Docker-based simulator for Reticulum mesh networks. Each simulated node runs a real, unmodified `rnsd` daemon in its own container. Linux `tc/netem` shapes traffic to simulate physical media (LoRa, WiFi, HaLow, packet radio, satellite). A FastAPI backend orchestrates the Docker infrastructure and serves a React SPA for real-time visualization and scenario building.

External Reticulum apps (Sideband, NomadNet, MeshChat) can connect to gateway nodes and interact with the simulated network as if it were real hardware.

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Browser                                                │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ Viewer Tab  │  │ Builder Tab  │  │ Profiles Tab  │   │
│  │ topology/map│  │ map + events │  │ CRUD          │   │
│  └──────┬───┬──┘  └──────┬───────┘  └───────┬───────┘   │
│         │   │            │                   │          │
│    MobX stores ◄── WebSocket (1Hz) ──────────┘          │
│         │                                               │
└─────────┼───────────────────────────────────────────────┘
          │ REST + WS
          ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI (:3000)           rnetsim/api/                 │
│  ┌────────────┐ ┌────────────┐ ┌─────────────────────┐  │
│  │ /api/scen. │ │ /api/sim.  │ │ /ws (broadcast)     │  │
│  │ /api/prof. │ │ /api/terr. │ │ polls health @ 1Hz  │  │
│  └─────┬──────┘ └─────┬──────┘ └─────────┬───────────┘  │
│        │              │                   │             │
│  ┌─────▼──────┐ ┌─────▼──────────────────▼───────────┐  │
│  │ File stores│ │ SimulationManager (mutex, 1 sim)   │  │
│  │ YAML + JSON│ │   → launch_scenario()              │  │
│  └────────────┘ │   → stop_scenario()                │  │
│                 │   → get_status()                   │  │
│                 │   → execute_event()                │  │
│                 └─────────────┬──────────────────────┘  │
└───────────────────────────────┼─────────────────────────┘
                                │ Docker API
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │ Container   │      │ Container   │      │ Container   │
   │ alpha       │◄────►│ bravo       │◄────►│ charlie     │
   │ rnsd + tc   │      │ rnsd + tc   │      │ rnsd + tc   │
   │ :8080 health│      │ :8080 health│      │ :8080 health│
   └─────────────┘      └─────────────┘      └─────────────┘
         Docker bridge network (rnetsim-{scenario})
```

## Directory Map

```
RNETSIM/
├── dev.py                      # Single-command dev bootstrap (python dev.py)
├── pyproject.toml              # Python build config, deps, entry points
├── Dockerfile.node             # Node container: python:3.11-slim + rnsd
├── Dockerfile.visualizer       # Production: multi-stage Node build + FastAPI
├── docker-compose.base.yaml    # Production compose (visualizer + Docker socket)
│
├── rnetsim/                    # Python package
│   ├── cli.py                  # Click CLI — all commands hit REST API via httpx
│   ├── config.py               # Path constants, ports, Docker image names
│   │
│   ├── fabric/                 # Simulation engine (no HTTP, no UI)
│   │   ├── launch.py           # Create network + containers + tc rules
│   │   ├── stop.py             # Teardown containers + network
│   │   ├── status.py           # Poll health endpoints, aggregate state
│   │   ├── inject.py           # Runtime events: kill, revive, partition, heal
│   │   ├── events.py           # Async event scheduler + duration parser
│   │   ├── state.py            # SimulationState dataclass (shared mutable)
│   │   ├── link_model.py       # 9 medium profiles (bandwidth/latency/loss/jitter)
│   │   ├── tc_shaper.py        # tc/netem command generation + docker exec
│   │   ├── geography.py        # Haversine, bearing, interpolation (pure math)
│   │   ├── radio_model.py      # FSPL, LoRa link budget, viability check
│   │   └── terrain.py          # DEM tile fetch, elevation, line-of-sight
│   │
│   ├── node/                   # Files copied INTO node containers
│   │   ├── entrypoint.sh       # Reads env vars, generates reticulum config, execs rnsd
│   │   ├── health.py           # HTTP health endpoint on :8080
│   │   └── telemetry.py        # Prometheus metrics on :9100
│   │
│   ├── gateway/
│   │   └── bridge.py           # Port mapping + Reticulum config snippet generation
│   │
│   ├── api/                    # FastAPI REST + WebSocket layer
│   │   ├── app.py              # create_app() factory, CORS, SPA serving, lifespan
│   │   ├── routes/
│   │   │   ├── scenarios.py    # CRUD: list, get, create, update, delete, duplicate
│   │   │   ├── profiles.py     # CRUD: list, get, create, update, delete (built-in protected)
│   │   │   ├── simulation.py   # launch, stop, status, inject
│   │   │   └── terrain.py      # elevation, LOS endpoints
│   │   ├── services/
│   │   │   ├── scenario_store.py    # Filesystem CRUD (built-in + user YAML)
│   │   │   ├── profile_store.py     # Built-in constants + user JSON files
│   │   │   └── simulation_manager.py # Mutex wrapper over fabric capabilities
│   │   ├── models/
│   │   │   ├── scenario.py     # Pydantic: Scenario, ScenarioNode, etc. + YAML I/O
│   │   │   ├── profile.py      # Pydantic: DeviceProfile + 8 BUILTIN_PROFILES
│   │   │   └── simulation.py   # Pydantic: NodeStatus, LinkStatus, SimulationStatus
│   │   └── ws/
│   │       └── realtime.py     # WebSocket broadcast loop (1Hz health poll)
│   │
│   └── scenarios/              # 8 built-in YAML scenarios (bundled with package)
│       ├── minimal.yaml        # 3 nodes — smoke test
│       ├── linear-chain.yaml   # 10 nodes — multi-hop
│       ├── star.yaml           # 9 nodes — central transport
│       ├── mountain-mesh.yaml  # 50 nodes — geographic with lat/lon
│       ├── heterogeneous.yaml  # Mixed media with bridge nodes
│       ├── partition-heal.yaml # Events at T+2m and T+5m
│       ├── sleep-wake.yaml     # Duty-cycling sensors
│       └── stress-100.yaml     # 100 nodes — scale test
│
├── web/                        # React SPA (Vite + TypeScript + Tailwind)
│   ├── src/
│   │   ├── App.tsx             # Tab router: Viewer | Builder | Profiles
│   │   ├── main.tsx            # React root mount
│   │   │
│   │   ├── schemas/            # Zod schemas → z.infer<> for TypeScript types
│   │   │   ├── scenario.ts
│   │   │   ├── profile.ts
│   │   │   └── simulation.ts
│   │   │
│   │   ├── api/                # Typed fetch wrappers (one file per resource)
│   │   │   ├── scenarios.ts
│   │   │   ├── profiles.ts
│   │   │   ├── simulation.ts
│   │   │   └── terrain.ts
│   │   │
│   │   ├── state/              # MobX observable stores
│   │   │   ├── simulation-store.ts  # WebSocket auto-reconnect, nodes, links, selection
│   │   │   ├── scenario-store.ts    # Scenario list CRUD
│   │   │   ├── profile-store.ts     # Profile list CRUD
│   │   │   └── builder-store.ts     # Builder mode, bbox, placed nodes, events
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── nav-bar.tsx      # Tabs + simulation status indicator
│   │   │   │   └── sidebar.tsx      # Collapsible context panel
│   │   │   ├── viewer/
│   │   │   │   ├── topology-graph.tsx    # D3 force-directed SVG
│   │   │   │   ├── geo-map.tsx          # MapLibre GL JS + PMTiles
│   │   │   │   ├── node-detail.tsx      # Selected node info + kill/revive
│   │   │   │   ├── metrics-dashboard.tsx # Aggregate stats cards
│   │   │   │   └── packet-inspector.tsx  # Stub for future packet view
│   │   │   ├── builder/
│   │   │   │   ├── builder-map.tsx       # MapLibre with mode-driven interactions
│   │   │   │   ├── device-profile-list.tsx # Profile cards sidebar
│   │   │   │   ├── device-profile-editor.tsx # Custom profile form
│   │   │   │   ├── bulk-placement.tsx    # Random/grid/cluster node placement
│   │   │   │   ├── event-timeline.tsx    # Event pills + add form
│   │   │   │   ├── scenario-info.tsx     # Name, description, save/launch
│   │   │   │   └── gateway-config.tsx    # Gateway port + config snippet
│   │   │   └── profiles/
│   │   │       └── profile-manager.tsx   # Full-page profile grid + CRUD
│   │   │
│   │   ├── lib/                # Shared utilities
│   │   │   ├── map-setup.ts    # PMTiles registration, createMap() factory
│   │   │   ├── map-layers.ts   # GeoJSON layer factories (nodes, links, ranges, LOS)
│   │   │   └── terrain-los.ts  # Client-side LOS batch API with caching
│   │   │
│   │   └── styles/
│   │       └── globals.css     # Tailwind directives, dark theme base
│   │
│   ├── cypress/                # Cypress e2e tests
│   │   ├── e2e/
│   │   │   ├── navigation.cy.ts
│   │   │   ├── viewer.cy.ts
│   │   │   ├── builder.cy.ts
│   │   │   ├── profiles.cy.ts
│   │   │   ├── simulation-lifecycle.cy.ts
│   │   │   └── responsive.cy.ts
│   │   ├── support/e2e.ts      # Custom commands: stubAPI, stubRunningSimulation
│   │   └── fixtures/           # Mock API responses
│   │
│   └── [config files]          # vite.config.ts, tailwind.config.js, tsconfig.json, etc.
│
└── tests/                      # pytest (Python unit + API integration)
    ├── conftest.py             # Fixtures: minimal_scenario, api_client, etc.
    ├── test_link_model.py
    ├── test_geography.py
    ├── test_radio_model.py
    ├── test_tc_shaper.py
    ├── test_events.py
    ├── test_scenario_model.py
    ├── test_profiles.py
    ├── test_topology.py
    ├── test_gateway.py
    ├── test_api_scenarios.py
    ├── test_api_profiles.py
    └── test_api_simulation.py
```

## Layers and Boundaries

The system has four layers. Each layer depends only on the layer below it.

### Layer 1: Fabric (`rnetsim/fabric/`)

The simulation engine. Pure Python, no HTTP, no UI. Talks to Docker and Linux `tc`. Every file exports a single capability — there are no god-classes.

**Key constraint:** `launch.py`, `stop.py`, `status.py`, and `inject.py` are the four lifecycle operations. They share state via `SimulationState`, a mutable dataclass. Only one simulation can run at a time.

**How containers work:** Each node is a `rnetsim-node` Docker container on a shared bridge network. The `entrypoint.sh` reads env vars (`RNETSIM_NODE_NAME`, `RNETSIM_INTERFACES` as JSON, etc.) and generates a Reticulum config file with `TCPServerInterface` (always) + `TCPClientInterface` entries (for each peer). `rnsd --service` runs as PID 1. Traffic shaping (`tc qdisc add ... netem ... tbf`) is applied inside each container via `docker exec` (requires `NET_ADMIN` capability).

**Topology:** `compute_link_topology()` in `launch.py` builds a full mesh within each medium group. Nodes sharing a medium type all interconnect via TCP. Nodes on different mediums don't link (unless a bridge node has both interfaces).

### Layer 2: API (`rnetsim/api/`)

FastAPI REST + WebSocket. A thin adapter over fabric capabilities — routes validate input, call fabric functions, and return JSON. The `SimulationManager` wraps fabric operations with an asyncio mutex.

**Data stores** are filesystem-based. Scenarios are YAML files in two directories: `rnetsim/scenarios/` (built-in, read-only) and `data/scenarios/` (user-created). Profiles are Python constants (built-in) + JSON files (custom). No database.

**WebSocket** at `/ws` broadcasts simulation state at 1Hz. The broadcast loop polls `get_status()`, which executes `docker exec` inside each container to hit the health endpoint. This is the only real-time data path.

### Layer 3: Frontend (`web/src/`)

React SPA with MobX state management and Zod-first schemas.

**State architecture:** Four MobX stores (`simulation-store`, `scenario-store`, `profile-store`, `builder-store`). All React components that read store data are wrapped with `observer()` from `mobx-react-lite`. The simulation store manages a WebSocket connection with exponential backoff reconnect.

**Type system:** Zod schemas in `schemas/` are the source of truth. TypeScript types are derived via `z.infer<typeof Schema>`. API fetch wrappers in `api/` return these types.

**Visualization:** Two rendering engines — D3 force-directed graph for topology view (D3 owns the SVG via `useRef` + `useEffect`), and MapLibre GL JS for geographic view (PMTiles from Protomaps CDN, GeoJSON sources updated from MobX stores).

### Layer 4: CLI (`rnetsim/cli.py`)

Click CLI. The binary IS the identity. All commands except `serve` and `doctor` hit the REST API via httpx — the CLI never touches Docker directly. `serve` runs the FastAPI app via uvicorn. `doctor` checks the local environment using the `[OK]/[SKIP]/[TODO]/[!!]` convergence pattern.

## Data Flow: Launching a Simulation

```
User selects scenario in UI dropdown
  → simulationStore.launch("minimal")
    → POST /api/simulation/launch {scenario: "minimal"}
      → SimulationManager.launch()
        → scenario_store.get_scenario("minimal")  # load YAML
        → launch_scenario(scenario, state)
          → docker network create rnetsim-minimal
          → compute_link_topology(scenario)  # full mesh per medium
          → for each node:
              build_env_vars(node, topology)
              docker containers.run(rnetsim-node, env=..., cap_add=NET_ADMIN)
              # Inside container: entrypoint.sh generates config, starts rnsd
          → for each node:
              apply_shaping(container, link_profile)
              # docker exec: tc qdisc add ... netem + tbf
          → schedule events (if any)
          → state.is_running = True
        → return {status: "launched"}
    → WebSocket broadcast loop starts sending state at 1Hz
      → get_status() polls each container health via docker exec
    → simulationStore updates nodes/links from WebSocket messages
    → topology-graph.tsx re-renders via observer()
```

## Data Flow: Builder → Scenario → Launch

```
User in Builder tab:
  1. Types scenario name + description (→ builderStore)
  2. Selects a profile from sidebar (→ builderStore.selectedProfileId)
  3. Draws a bounding box on map (→ builderStore.bbox)
  4. Clicks "Place 20 Nodes" (→ bulk-placement algo → builderStore.addNode() x20)
  5. Adds events via timeline (→ builderStore.addEvent())
  6. Clicks "Save" →
     scenario-info.tsx buildScenario() converts builder state to Scenario type
     → POST /api/scenarios (creates YAML file)
  7. Clicks "Launch" →
     buildScenario() + POST /api/scenarios + POST /api/simulation/launch
```

## Key Design Decisions

**Real rnsd, not a simulator.** Every node runs the actual Reticulum daemon. No protocol reimplementation. This means the simulator is always protocol-accurate, but convergence takes real time (announces propagate at Reticulum's pace).

**tc/netem inside containers.** Traffic shaping happens at the Linux kernel level inside each container. The two-qdisc stack (`netem` for latency/jitter/loss, `tbf` for bandwidth limiting) accurately models physical media. Minimum burst is 1540 bytes to prevent low-bandwidth profiles (293 bps LoRa SF12) from dropping all packets.

**One simulation at a time.** `SimulationManager` holds a single `SimulationState` protected by an asyncio mutex. This is intentional simplicity — multi-simulation support would require container namespace isolation.

**Filesystem, not database.** Scenarios are YAML files. Profiles are JSON files. The built-in scenarios ship inside the Python package (`rnetsim/scenarios/`). User data goes in `data/`. This makes the system trivially inspectable and version-controllable.

**MobX over hooks-based state.** Observable stores with `observer()` wrapped components, per project conventions. Zod schemas are the type source of truth, not hand-written interfaces.

**WebSocket is read-only.** The frontend sends no meaningful messages over WebSocket — it's a pure broadcast channel. All mutations go through REST endpoints.

## Medium Profiles

| Medium          | Bandwidth | Latency | Loss | Jitter | Use Case                     |
| --------------- | --------- | ------- | ---- | ------ | ---------------------------- |
| `lora_sf7_125`  | 5.5 kbps  | 50ms    | 0%   | 50ms   | Short-range, high throughput |
| `lora_sf8_125`  | 3.1 kbps  | 100ms   | 0%   | 100ms  | Default LoRa (balanced)      |
| `lora_sf12_125` | 293 bps   | 2000ms  | 0%   | 2000ms | Long-range, low throughput   |
| `wifi_local`    | 50 Mbps   | 2ms     | 0%   | 1ms    | Local WiFi                   |
| `ethernet`      | 1 Gbps    | 0.5ms   | 0%   | 0.1ms  | Wired LAN                    |
| `internet`      | 50 Mbps   | 50ms    | 0.1% | 20ms   | TCP/IP over internet         |
| `packet_radio`  | 1.2 kbps  | 500ms   | 2%   | 200ms  | Legacy AX.25 TNC             |
| `satellite`     | 64 kbps   | 800ms   | 0.5% | 100ms  | LEO satellite link           |
| `halow_4mhz`    | 15 Mbps   | 5ms     | 0%   | 2ms    | Wi-Fi HaLow (sub-GHz)        |

## Radio Propagation Model

Used when nodes have lat/lon coordinates. Free-space path loss:

```
FSPL(dB) = 20*log10(d_m) + 20*log10(f_hz) - 147.55
```

LoRa receiver sensitivity per SF: SF7 = -123 dBm, SF8 = -126 dBm, SF12 = -137 dBm. An obstruction penalty of 30 dB is added when line-of-sight is blocked (determined by terrain elevation profile from Mapzen Terrain-RGB DEM tiles).

## Gateway Architecture

Gateway nodes expose their Reticulum TCP port (4242) to the Docker host via port mapping. External apps add a `TCPClientInterface` pointing to `localhost:{mapped_port}`. The UI displays a copy-paste config snippet:

```ini
[[RNETSIM Gateway]]
  type = TCPClientInterface
  target_host = localhost
  target_port = 14242
```

## Testing Strategy

**Python (pytest):** Unit tests for every fabric module (link model, geography, radio model, tc shaper, events, topology). Model validation tests for Pydantic scenarios and profiles. API integration tests using FastAPI's `TestClient`. All 8 built-in YAML scenarios are validated on every run.

**Frontend (Cypress):** E2E tests with stubbed API (`cy.intercept`). Covers navigation, viewer (idle + running states), builder (sidebar, events, placement), profiles (CRUD), simulation lifecycle (launch → observe → stop), and responsive layout. No backend required — all API responses are fixtures.

## Ports

| Port | Service             | Context                                    |
| ---- | ------------------- | ------------------------------------------ |
| 3000 | FastAPI (API + SPA) | Host                                       |
| 5173 | Vite dev server     | Host (dev only)                            |
| 4242 | Reticulum TCP       | Inside containers (+ gateway host mapping) |
| 8080 | Health endpoint     | Inside containers                          |
| 9100 | Prometheus metrics  | Inside containers                          |

## Adding a New Feature: Checklist

1. **New medium type?** Add to `fabric/link_model.py` PROFILES dict. Update `VALID_MEDIUMS`. Add a YAML scenario exercising it.
2. **New event action?** Add handler in `fabric/inject.py`. Add to `EVENT_COLORS`/`EVENT_LABELS` in `builder/event-timeline.tsx`. Add Cypress test.
3. **New API endpoint?** Add route in `api/routes/`. Wire in `api/app.py`. Add pytest test in `tests/test_api_*.py`.
4. **New builder feature?** Add MobX observable to `state/builder-store.ts`. Create component in `components/builder/`. Wire in `App.tsx`. Add Cypress test.
5. **New built-in profile?** Add to `BUILTIN_PROFILES` in `api/models/profile.py`. Update fixtures in `cypress/fixtures/profiles.json`.
