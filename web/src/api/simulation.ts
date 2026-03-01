import type { SimulationStatus } from "../schemas/simulation";

const BASE = "/api/simulation";

export async function launchSimulation(scenario: string): Promise<void> {
  const res = await fetch(`${BASE}/launch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function stopSimulation(): Promise<void> {
  const res = await fetch(`${BASE}/stop`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
}

export async function fetchSimulationStatus(): Promise<SimulationStatus> {
  const res = await fetch(`${BASE}/status`);
  return res.json();
}

export async function injectEvent(
  action: string,
  target?: string,
  params?: Record<string, unknown>,
): Promise<void> {
  const res = await fetch(`${BASE}/inject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, target, params }),
  });
  if (!res.ok) throw new Error(await res.text());
}
