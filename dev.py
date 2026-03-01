#!/usr/bin/env python3
"""RNETSIM developer bootstrap — single command to convergence.

    python dev.py

Re-runnable. Each step checks, auto-fixes if possible, prompts otherwise.
Uses [OK]/[SKIP]/[TODO]/[!!] convergence output.

After convergence:
  - Python venv active with rnetsim installed editable
  - Node deps installed
  - Docker node image built
  - API server running on resolved port
  - Vite dev server running on resolved port
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
WEB = ROOT / "web"
VENV = ROOT / ".venv"
DATA = ROOT / "data"
LOGS = ROOT / ".logs"

NODE_IMAGE = "rnetsim-node"

# Default ports — may be adjusted by resolve_ports()
DEFAULT_API_PORT = 3000
DEFAULT_VITE_PORT = 5173
VITE_OFFSET = 173  # Vite = base + 173 for fallback pairs

# Resolved at startup
api_port: int = DEFAULT_API_PORT
vite_port: int = DEFAULT_VITE_PORT

# ── pretty output ──────────────────────────────────────────────────────────────

GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}[OK]{RESET}   {msg}")


def skip(msg: str) -> None:
    print(f"  {CYAN}[SKIP]{RESET} {msg}")


def todo(msg: str) -> None:
    print(f"  {YELLOW}[TODO]{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}[!!]{RESET}   {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}[!!]{RESET}   {msg}")


def heading(msg: str) -> None:
    print(f"\n{BOLD}{msg}{RESET}")


def ask(prompt: str, default: str = "y") -> bool:
    hint = "Y/n" if default == "y" else "y/N"
    try:
        resp = input(f"  {DIM}→ {prompt} [{hint}]: {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default == "y"
    if not resp:
        return default == "y"
    return resp.startswith("y")


def port_in_use(port: int) -> bool:
    for family, addr in [(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")]:
        with socket.socket(family, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex((addr, port)) == 0:
                return True
    return False


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def run_or_die(cmd: list[str], msg: str, **kw) -> None:
    result = run(cmd, **kw)
    if result.returncode != 0:
        fail(f"{msg}")
        if result.stderr:
            for line in result.stderr.strip().splitlines()[:5]:
                print(f"         {DIM}{line}{RESET}")
        sys.exit(1)


# ── port identity checks ─────────────────────────────────────────────────────

def is_rnetsim_api(port: int) -> bool:
    """Check if the service on this port is our RNETSIM API server."""
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/simulation/status", timeout=2)
        body = r.read().decode()
        return '"running"' in body
    except Exception:
        return False


def is_rnetsim_vite(port: int) -> bool:
    """Check if the service on this port is our RNETSIM Vite dev server.

    Vite serves web/public/ files at the root — we check for our identity file.
    """
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}/rnetsim.id", timeout=2)
        body = r.read().decode().strip()
        return body == "rnetsim"
    except Exception:
        return False


def _port_usable(port: int, identity_fn) -> str:
    """Check port state. Returns 'free', 'ours', or 'blocked'."""
    if not port_in_use(port):
        return "free"
    if identity_fn(port):
        return "ours"
    return "blocked"


def resolve_ports() -> tuple[int, int]:
    """Find available ports for API and Vite, respecting existing RNETSIM instances.

    Strategy:
      1. Try default pair (3000, 5173)
      2. If a port is occupied, health-check it — if it's RNETSIM, reuse it
      3. If it's something else, note the collision and try fallback pairs:
         (4000, 4173), (5000, 5173), (6000, 6173), ...
      4. Both ports in the pair must be free or already ours
    """
    global api_port, vite_port
    heading("Port resolution")

    # Try defaults first
    api_state = _port_usable(DEFAULT_API_PORT, is_rnetsim_api)
    vite_state = _port_usable(DEFAULT_VITE_PORT, is_rnetsim_vite)

    if api_state in ("free", "ours") and vite_state in ("free", "ours"):
        api_port = DEFAULT_API_PORT
        vite_port = DEFAULT_VITE_PORT
        _report_port(DEFAULT_API_PORT, "API", api_state)
        _report_port(DEFAULT_VITE_PORT, "Vite", vite_state)
        return api_port, vite_port

    # Report what's blocking us
    if api_state == "blocked":
        warn(f":{DEFAULT_API_PORT} occupied by another service (not RNETSIM)")
    if vite_state == "blocked":
        warn(f":{DEFAULT_VITE_PORT} occupied by another service (not RNETSIM)")

    # Walk up in 1000-port increments starting at 4000
    for base in range(4000, 10000, 1000):
        candidate_api = base
        candidate_vite = base + VITE_OFFSET
        a = _port_usable(candidate_api, is_rnetsim_api)
        v = _port_usable(candidate_vite, is_rnetsim_vite)
        if a in ("free", "ours") and v in ("free", "ours"):
            api_port = candidate_api
            vite_port = candidate_vite
            ok(f"Resolved API :{api_port}, Vite :{vite_port}")
            return api_port, vite_port

    fail("Could not find two free ports between 4000-10000")
    sys.exit(1)


def _report_port(port: int, label: str, state: str) -> None:
    if state == "free":
        ok(f":{port} available ({label})")
    elif state == "ours":
        skip(f":{port} is RNETSIM ({label}) — reusing")


# ── convergence steps ──────────────────────────────────────────────────────────

def check_python() -> None:
    heading("Python")
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail(f"Python >= 3.11 required (found {v.major}.{v.minor})")
        sys.exit(1)


def check_venv() -> None:
    heading("Virtual environment")
    pip = VENV / "bin" / "pip"

    if VENV.exists() and pip.exists():
        skip(f".venv exists at {VENV}")
    else:
        if ask("Create .venv and install deps?"):
            print(f"  {DIM}→ Creating venv...{RESET}")
            subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
            ok("Created .venv")
        else:
            todo("Create venv manually: python -m venv .venv")
            return

    # Install editable with dev extras
    pip_exe = str(VENV / "bin" / "pip")

    # Check if rnetsim is installed
    result = run([pip_exe, "show", "rnetsim"])
    if result.returncode == 0:
        skip("rnetsim installed (editable)")
    else:
        if ask("Install rnetsim in editable mode with dev deps?"):
            print(f"  {DIM}→ pip install -e '.[dev]' ...{RESET}")
            run_or_die(
                [pip_exe, "install", "-e", ".[dev]"],
                "pip install failed",
                cwd=str(ROOT),
            )
            ok("Installed rnetsim + dev deps")
        else:
            todo("Run: .venv/bin/pip install -e '.[dev]'")


def check_node() -> None:
    heading("Node.js")
    node = shutil.which("node")
    if not node:
        fail("Node.js not found — install Node >= 18")
        print(f"         {DIM}https://nodejs.org or: brew install node{RESET}")
        return

    result = run([node, "--version"])
    version = result.stdout.strip().lstrip("v")
    major = int(version.split(".")[0])
    if major >= 18:
        ok(f"Node {version}")
    else:
        fail(f"Node >= 18 required (found {version})")
        return

    npm = shutil.which("npm")
    if not npm:
        fail("npm not found")
        return

    # Check node_modules
    nm = WEB / "node_modules"
    if nm.exists() and (nm / ".package-lock.json").exists():
        skip("node_modules present")
    else:
        if ask("Run npm install in web/?"):
            print(f"  {DIM}→ npm install ...{RESET}")
            run_or_die([npm, "install"], "npm install failed", cwd=str(WEB))
            ok("npm install complete")
        else:
            todo("Run: cd web && npm install")


def check_docker() -> None:
    heading("Docker")
    docker = shutil.which("docker")
    if not docker:
        fail("Docker not found — install Docker Desktop")
        print(f"         {DIM}https://www.docker.com/products/docker-desktop{RESET}")
        return

    result = run([docker, "info"])
    if result.returncode != 0:
        fail("Docker daemon not responding — start Docker Desktop")
        return
    ok("Docker daemon running")

    # Check node image
    result = run([docker, "image", "inspect", NODE_IMAGE])
    if result.returncode == 0:
        skip(f"{NODE_IMAGE} image exists")
    else:
        if ask(f"Build {NODE_IMAGE} Docker image?"):
            print(f"  {DIM}→ docker build -t {NODE_IMAGE} -f Dockerfile.node . ...{RESET}")
            build = subprocess.run(
                [docker, "build", "-t", NODE_IMAGE, "-f", "Dockerfile.node", "."],
                cwd=str(ROOT),
            )
            if build.returncode == 0:
                ok(f"{NODE_IMAGE} image built")
            else:
                fail("Docker build failed — check Dockerfile.node")
        else:
            todo(f"Run: docker build -t {NODE_IMAGE} -f Dockerfile.node .")


def check_dirs() -> None:
    heading("Data directories")
    for d, label in [
        (DATA, "data/"),
        (DATA / "scenarios", "data/scenarios/"),
        (DATA / "profiles", "data/profiles/"),
        (DATA / "terrain-cache", "data/terrain-cache/"),
        (LOGS, ".logs/"),
    ]:
        if d.exists():
            skip(f"{label}")
        else:
            d.mkdir(parents=True, exist_ok=True)
            ok(f"Created {label}")


def start_servers() -> tuple[subprocess.Popen | None, subprocess.Popen | None]:
    heading("Services")
    api_proc = None
    vite_proc = None

    # API server
    if port_in_use(api_port) and is_rnetsim_api(api_port):
        skip(f"RNETSIM API already running on :{api_port}")
    elif port_in_use(api_port):
        fail(f":{api_port} unexpectedly occupied after port resolution")
    else:
        rnetsim_bin = VENV / "bin" / "rnetsim"
        if not rnetsim_bin.exists():
            cmd = [str(VENV / "bin" / "python"), "-m", "rnetsim", "serve", "--port", str(api_port)]
        else:
            cmd = [str(rnetsim_bin), "serve", "--port", str(api_port)]

        api_proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=open(LOGS / "api.log", "w"),
            stderr=subprocess.STDOUT,
        )
        for _ in range(30):
            if port_in_use(api_port):
                break
            time.sleep(0.5)

        if port_in_use(api_port):
            ok(f"API server started (PID {api_proc.pid}, log: .logs/api.log)")
        else:
            fail("API server failed to start — check .logs/api.log")

    # Vite dev server
    if port_in_use(vite_port) and is_rnetsim_vite(vite_port):
        skip(f"RNETSIM Vite already running on :{vite_port}")
    elif port_in_use(vite_port):
        fail(f":{vite_port} unexpectedly occupied after port resolution")
    else:
        npm = shutil.which("npm")
        if npm:
            # Pass ports as env vars so vite.config.ts picks them up
            vite_env = os.environ.copy()
            vite_env["RNETSIM_API_PORT"] = str(api_port)
            vite_env["RNETSIM_VITE_PORT"] = str(vite_port)

            vite_proc = subprocess.Popen(
                [npm, "run", "dev"],
                cwd=str(WEB),
                env=vite_env,
                stdout=open(LOGS / "vite.log", "w"),
                stderr=subprocess.STDOUT,
            )
            for _ in range(20):
                if port_in_use(vite_port):
                    break
                time.sleep(0.5)

            if port_in_use(vite_port):
                ok(f"Vite dev server started (PID {vite_proc.pid}, log: .logs/vite.log)")
            else:
                fail("Vite dev server failed to start — check .logs/vite.log")
        else:
            todo(f"npm not found — install Node to start Vite dev server")

    return api_proc, vite_proc


def print_dev_menu(api_proc, vite_proc) -> None:
    """The 'd' key menu — shows all links, pids, and commands."""
    print(f"\n  {BOLD}RNETSIM Developer Environment{RESET}")
    print(f"  {'─' * 48}")
    print()

    # Service status
    api_up = port_in_use(api_port)
    vite_up = port_in_use(vite_port)
    docker_ok = shutil.which("docker") and run(["docker", "info"]).returncode == 0

    print(f"  {BOLD}Services:{RESET}")
    print(f"    API server   {GREEN}running{RESET} :{api_port}" if api_up else f"    API server   {RED}stopped{RESET}")
    print(f"    Vite dev     {GREEN}running{RESET} :{vite_port}" if vite_up else f"    Vite dev     {RED}stopped{RESET}")
    print(f"    Docker       {GREEN}running{RESET}" if docker_ok else f"    Docker       {RED}stopped{RESET}")
    print()

    # Non-default port notice
    if api_port != DEFAULT_API_PORT or vite_port != DEFAULT_VITE_PORT:
        print(f"  {YELLOW}Note:{RESET} Using non-default ports (defaults {DEFAULT_API_PORT}/{DEFAULT_VITE_PORT} were occupied)")
        print()

    # Links
    print(f"  {BOLD}Links:{RESET}")
    if vite_up:
        print(f"    {GREEN}Web UI:{RESET}        http://localhost:{vite_port}")
    if api_up:
        print(f"    {GREEN}API:{RESET}           http://localhost:{api_port}/api/scenarios")
        print(f"    {GREEN}WebSocket:{RESET}     ws://localhost:{api_port}/ws")
    print()

    # PIDs
    pids = []
    if api_proc and api_proc.poll() is None:
        pids.append(f"API={api_proc.pid}")
    if vite_proc and vite_proc.poll() is None:
        pids.append(f"Vite={vite_proc.pid}")
    if pids:
        print(f"  {BOLD}PIDs:{RESET} {', '.join(pids)}")
        print()

    # Commands
    print(f"  {BOLD}CLI commands:{RESET}")
    print(f"    {DIM}.venv/bin/rnetsim doctor{RESET}       check environment")
    print(f"    {DIM}.venv/bin/rnetsim up minimal{RESET}   launch a scenario")
    print(f"    {DIM}.venv/bin/rnetsim status{RESET}       node status table")
    print(f"    {DIM}.venv/bin/rnetsim down{RESET}         stop simulation")
    print(f"    {DIM}.venv/bin/pytest tests/{RESET}        run unit tests")
    print(f"    {DIM}cd web && npm run cy:open{RESET}      Cypress e2e tests")
    print()

    # Keystrokes
    print(f"  {BOLD}Keystrokes:{RESET}")
    print(f"    {CYAN}d{RESET}  show this dev menu")
    print(f"    {CYAN}t{RESET}  run pytest")
    print(f"    {CYAN}o{RESET}  open browser to web UI")
    print(f"    {CYAN}l{RESET}  tail API log")
    print(f"    {CYAN}r{RESET}  restart servers")
    print(f"    {CYAN}q{RESET}  quit (stop all services)")
    print()


def _get_key() -> str | None:
    """Read a single keypress without requiring Enter (Unix only)."""
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if select.select([sys.stdin], [], [], 0.5)[0]:
            ch = sys.stdin.read(1)
            return ch
    except (termios.error, ValueError):
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return None


def _handle_key(key: str, api_proc, vite_proc) -> bool:
    """Handle a keystroke. Returns False to quit."""
    if key == "d":
        print_dev_menu(api_proc, vite_proc)

    elif key == "t":
        print(f"\n  {DIM}Running pytest...{RESET}\n")
        pytest_bin = VENV / "bin" / "pytest"
        if pytest_bin.exists():
            subprocess.run([str(pytest_bin), "tests/", "-v", "--tb=short"], cwd=str(ROOT))
        else:
            fail("pytest not found — run: .venv/bin/pip install -e '.[dev]'")
        print()

    elif key == "o":
        import webbrowser
        url = f"http://localhost:{vite_port}" if port_in_use(vite_port) else f"http://localhost:{api_port}"
        print(f"\n  {DIM}Opening {url}...{RESET}")
        webbrowser.open(url)

    elif key == "l":
        log = LOGS / "api.log"
        if log.exists():
            print(f"\n  {DIM}── .logs/api.log (last 20 lines) ──{RESET}")
            lines = log.read_text().splitlines()
            for line in lines[-20:]:
                print(f"  {DIM}{line}{RESET}")
            print(f"  {DIM}────────────────────────────────────{RESET}\n")
        else:
            fail("No API log found")

    elif key == "r":
        print(f"\n  {DIM}Restarting servers...{RESET}")
        return "restart"

    elif key in ("q", "\x03"):  # q or Ctrl+C
        return False

    return True


def _shutdown(api_proc, vite_proc) -> None:
    """Gracefully stop background processes."""
    if api_proc and api_proc.poll() is None:
        api_proc.terminate()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        ok("API server stopped")
    if vite_proc and vite_proc.poll() is None:
        vite_proc.terminate()
        try:
            vite_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            vite_proc.kill()
        ok("Vite dev server stopped")


def main() -> None:
    print(f"\n{BOLD}{'═' * 50}{RESET}")
    print(f"{BOLD}  RNETSIM — converge developer environment{RESET}")
    print(f"{BOLD}{'═' * 50}{RESET}")

    check_python()
    check_venv()
    check_node()
    check_docker()
    check_dirs()
    resolve_ports()
    api_proc, vite_proc = start_servers()

    # Show dev menu on first launch
    print_dev_menu(api_proc, vite_proc)

    # Interactive loop if we have background services
    if not (api_proc or vite_proc):
        return

    print(f"  {DIM}Press 'd' for dev menu, 'q' to quit{RESET}\n")

    try:
        while True:
            # Check children are alive
            if api_proc and api_proc.poll() is not None:
                fail("API server exited — check .logs/api.log")
                break
            if vite_proc and vite_proc.poll() is not None:
                fail("Vite dev server exited — check .logs/vite.log")
                break

            key = _get_key()
            if key is None:
                continue

            result = _handle_key(key, api_proc, vite_proc)

            if result is False:
                break
            elif result == "restart":
                _shutdown(api_proc, vite_proc)
                api_proc, vite_proc = start_servers()
                print_dev_menu(api_proc, vite_proc)
                print(f"  {DIM}Press 'd' for dev menu, 'q' to quit{RESET}\n")

    except KeyboardInterrupt:
        print(f"\n  {DIM}Shutting down...{RESET}")
    finally:
        _shutdown(api_proc, vite_proc)


if __name__ == "__main__":
    main()
