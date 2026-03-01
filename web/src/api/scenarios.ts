import type { Scenario, ScenarioSummary } from "../schemas/scenario";

const BASE = "/api/scenarios";

export async function fetchScenarios(): Promise<ScenarioSummary[]> {
  const res = await fetch(BASE);
  return res.json();
}

export async function fetchScenario(name: string): Promise<Scenario> {
  const res = await fetch(`${BASE}/${name}`);
  if (!res.ok) throw new Error(`Scenario '${name}' not found`);
  return res.json();
}

export async function createScenario(scenario: Scenario): Promise<void> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenario),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function updateScenario(
  name: string,
  scenario: Scenario,
): Promise<void> {
  const res = await fetch(`${BASE}/${name}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenario),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function deleteScenario(name: string): Promise<void> {
  const res = await fetch(`${BASE}/${name}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export async function duplicateScenario(name: string): Promise<string> {
  const res = await fetch(`${BASE}/${name}/duplicate`, { method: "POST" });
  const data = await res.json();
  return data.new_name;
}

export async function exportScenarioYaml(name: string): Promise<string> {
  const res = await fetch(`${BASE}/${name}/yaml`);
  return res.text();
}
