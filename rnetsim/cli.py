"""RNETSIM CLI — the binary IS the identity.

Subcommands map 1:1 to capabilities. The CLI is a surface, not a brain —
it parses arguments, resolves the requested capability, and delegates.
Logic does not live here. All commands hit the REST API via httpx.
"""

import click

from rnetsim.config import VISUALIZER_PORT


def _api_url(port: int = VISUALIZER_PORT) -> str:
    return f"http://localhost:{port}"


def _api_get(path: str) -> dict | list | None:
    import httpx

    try:
        r = httpx.get(f"{_api_url()}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        click.secho("Cannot reach RNETSIM server. Is `rnetsim serve` running?", fg="red")
        raise SystemExit(1)
    except httpx.HTTPStatusError as e:
        click.secho(f"API error: {e.response.status_code} — {e.response.text}", fg="red")
        raise SystemExit(1)


def _api_post(path: str, json_data: dict | None = None) -> dict | list | None:
    import httpx

    try:
        r = httpx.post(f"{_api_url()}{path}", json=json_data, timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        click.secho("Cannot reach RNETSIM server. Is `rnetsim serve` running?", fg="red")
        raise SystemExit(1)
    except httpx.HTTPStatusError as e:
        click.secho(f"API error: {e.response.status_code} — {e.response.text}", fg="red")
        raise SystemExit(1)


@click.group()
@click.version_option(package_name="rnetsim")
def main() -> None:
    """RNETSIM — Reticulum Network Simulator.

    Docker-based simulation of heterogeneous Reticulum mesh networks
    with real-time visualization, bandwidth shaping, and geographic modeling.
    """


@main.command()
@click.option("--host", default="0.0.0.0", help="Bind address")
@click.option("--port", default=3000, type=int, help="Port for API + SPA")
def serve(host: str, port: int) -> None:
    """Start the API server and web UI."""
    import uvicorn

    uvicorn.run(
        "rnetsim.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        log_level="info",
    )


@main.command()
@click.argument("scenario")
def up(scenario: str) -> None:
    """Start a simulation scenario."""
    click.echo(f"Launching scenario: {scenario}")
    result = _api_post("/api/simulation/launch", {"scenario": scenario})
    if result:
        click.secho(f"Scenario '{scenario}' launched.", fg="green")


@main.command()
def down() -> None:
    """Stop the running simulation."""
    click.echo("Stopping simulation...")
    result = _api_post("/api/simulation/stop")
    if result:
        click.secho("Simulation stopped.", fg="green")


@main.command()
def status() -> None:
    """Show node status table."""
    data = _api_get("/api/simulation/status")
    if not data:
        click.echo("No simulation running.")
        return

    if not data.get("running"):
        click.echo("No simulation running.")
        return

    click.echo(f"Scenario: {data.get('scenario_name', '?')}")
    click.echo(f"Nodes:    {data.get('node_count', 0)}")
    click.echo()

    nodes = data.get("nodes", [])
    if not nodes:
        click.echo("  No nodes.")
        return

    # Table header
    click.echo(f"  {'Name':<24} {'Role':<12} {'Status':<10} {'Paths':<8} {'Announces':<10}")
    click.echo(f"  {'─'*24} {'─'*12} {'─'*10} {'─'*8} {'─'*10}")

    for n in nodes:
        name = n.get("name", "?")
        role = n.get("role", "?")
        node_status = n.get("status", "offline")
        is_healthy = node_status == "healthy"
        status_str = click.style("healthy", fg="green") if is_healthy else click.style(node_status, fg="red")
        paths = n.get("path_count", 0)
        announces = n.get("announce_count", 0)
        click.echo(f"  {name:<24} {role:<12} {status_str:<10} {paths:<8} {announces:<10}")


@main.command()
def doctor() -> None:
    """Check environment and guide to working state.

    Uses [OK]/[SKIP]/[TODO]/[!!] convergence pattern.
    """
    import shutil
    import subprocess

    checks: list[tuple[str, str]] = []

    # Docker daemon
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=10
        )
        if result.returncode == 0:
            checks.append(("[OK]", "Docker daemon running"))
        else:
            checks.append(("[!!]", "Docker not responding — start Docker Desktop"))
    else:
        checks.append(("[!!]", "Docker not found — install Docker Desktop"))

    # Node image
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "image", "inspect", "rnetsim-node"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            checks.append(("[OK]", "rnetsim-node image built"))
        else:
            checks.append(
                ("[TODO]", "Node image not found — run: docker build -t rnetsim-node -f Dockerfile.node .")
            )

    # API server
    try:
        import httpx

        r = httpx.get(f"{_api_url()}/api/scenarios", timeout=3)
        if r.status_code == 200:
            checks.append(("[OK]", f"API server reachable at port {VISUALIZER_PORT}"))
        else:
            checks.append(("[TODO]", f"API server returned {r.status_code} — run: rnetsim serve"))
    except Exception:
        checks.append(("[TODO]", f"API server not running on port {VISUALIZER_PORT} — run: rnetsim serve"))

    # Data directories
    from rnetsim.config import DATA_DIR, SCENARIOS_DIR, PROFILES_DIR

    for d, label in [
        (DATA_DIR, "Data directory"),
        (SCENARIOS_DIR, "Scenarios directory"),
        (PROFILES_DIR, "Profiles directory"),
    ]:
        if d.exists():
            checks.append(("[SKIP]", f"{label} exists: {d}"))
        else:
            d.mkdir(parents=True, exist_ok=True)
            checks.append(("[OK]", f"{label} created: {d}"))

    # Port availability
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(("localhost", VISUALIZER_PORT))
        sock.close()
        checks.append(("[SKIP]", f"Port {VISUALIZER_PORT} in use (server running)"))
    except (ConnectionRefusedError, OSError):
        checks.append(("[OK]", f"Port {VISUALIZER_PORT} available"))

    # Print results
    for status_tag, message in checks:
        if status_tag == "[OK]":
            click.secho(f"  {status_tag}  {message}", fg="green")
        elif status_tag == "[SKIP]":
            click.secho(f"  {status_tag} {message}", fg="cyan")
        elif status_tag == "[TODO]":
            click.secho(f"  {status_tag} {message}", fg="yellow")
        elif status_tag == "[!!]":
            click.secho(f"  {status_tag}   {message}", fg="red")

    # Summary
    ok_count = sum(1 for s, _ in checks if s in ("[OK]", "[SKIP]"))
    todo_count = sum(1 for s, _ in checks if s == "[TODO]")
    fail_count = sum(1 for s, _ in checks if s == "[!!]")
    click.echo(f"\n  {ok_count} ok, {todo_count} todo, {fail_count} issues")


@main.command()
def viz() -> None:
    """Open the visualizer in a browser."""
    import webbrowser

    webbrowser.open(f"http://localhost:{VISUALIZER_PORT}")


@main.group()
def inject() -> None:
    """Inject runtime events into a running simulation."""


@inject.command("kill")
@click.argument("node")
def inject_kill(node: str) -> None:
    """Kill a node."""
    click.echo(f"Killing node: {node}")
    _api_post("/api/simulation/inject", {"action": "kill_node", "target": node})
    click.secho(f"Node '{node}' killed.", fg="yellow")


@inject.command("revive")
@click.argument("node")
def inject_revive(node: str) -> None:
    """Revive a killed node."""
    click.echo(f"Reviving node: {node}")
    _api_post("/api/simulation/inject", {"action": "revive_node", "target": node})
    click.secho(f"Node '{node}' revived.", fg="green")


@inject.command("partition")
@click.argument("group_a")
@click.argument("group_b")
def inject_partition(group_a: str, group_b: str) -> None:
    """Partition network between two node groups (comma-separated names)."""
    click.echo(f"Partitioning: {group_a} <-> {group_b}")
    _api_post("/api/simulation/inject", {
        "action": "partition",
        "target": group_a,
        "params": {"group_b": group_b},
    })
    click.secho("Partition applied.", fg="yellow")


@inject.command("heal")
def inject_heal() -> None:
    """Heal all network partitions."""
    click.echo("Healing partitions...")
    _api_post("/api/simulation/inject", {"action": "heal"})
    click.secho("Partitions healed.", fg="green")


@main.group()
def scenario() -> None:
    """Manage scenarios."""


@scenario.command("list")
def scenario_list() -> None:
    """List available scenarios."""
    scenarios = _api_get("/api/scenarios")
    if not scenarios:
        click.echo("No scenarios found.")
        return

    click.echo(f"  {'Name':<24} {'Nodes':<8} {'Events':<8} {'Description'}")
    click.echo(f"  {'─'*24} {'─'*8} {'─'*8} {'─'*40}")

    for s in scenarios:
        name = s.get("name", "?")
        node_count = s.get("node_count", 0)
        event_count = s.get("event_count", 0)
        desc = s.get("description", "")[:40]
        click.echo(f"  {name:<24} {node_count:<8} {event_count:<8} {desc}")


@scenario.command("validate")
@click.argument("path", type=click.Path(exists=True))
def scenario_validate(path: str) -> None:
    """Validate a scenario YAML file."""
    from rnetsim.api.models.scenario import load_scenario_yaml

    try:
        scenario_obj = load_scenario_yaml(path)
        click.secho(f"  [OK] Valid scenario: {scenario_obj.name}", fg="green")
        click.echo(f"       {len(scenario_obj.nodes)} nodes, {len(scenario_obj.events)} events")
    except Exception as e:
        click.secho(f"  [!!] Invalid: {e}", fg="red")
        raise SystemExit(1)


@main.command()
@click.argument("node")
@click.option("--lines", "-n", default=50, help="Number of log lines")
def logs(node: str, lines: int) -> None:
    """Tail logs from a node container."""
    import docker as docker_lib

    try:
        client = docker_lib.from_env()
        container = client.containers.get(node)
        output = container.logs(tail=lines).decode("utf-8", errors="replace")
        click.echo(output)
    except docker_lib.errors.NotFound:
        click.secho(f"Container '{node}' not found.", fg="red")
        raise SystemExit(1)
    except docker_lib.errors.DockerException as e:
        click.secho(f"Docker error: {e}", fg="red")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
