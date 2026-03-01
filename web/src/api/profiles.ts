import type { DeviceProfile } from "../schemas/profile";

const BASE = "/api/profiles";

export async function fetchProfiles(): Promise<DeviceProfile[]> {
  const res = await fetch(BASE);
  return res.json();
}

export async function fetchProfile(id: string): Promise<DeviceProfile> {
  const res = await fetch(`${BASE}/${id}`);
  if (!res.ok) throw new Error(`Profile '${id}' not found`);
  return res.json();
}

export async function createProfile(profile: DeviceProfile): Promise<void> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function deleteProfile(id: string): Promise<void> {
  const res = await fetch(`${BASE}/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}
