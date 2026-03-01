const BASE = "/api/terrain";

export interface ElevationResult {
  lat: number;
  lon: number;
  elevation: number;
}

export interface LOSResult {
  clear: boolean;
  degraded?: boolean;
  clearance_min?: number;
  from: { lat: number; lon: number };
  to: { lat: number; lon: number };
}

export interface ElevationSample {
  distance: number;
  terrain_elevation: number;
  los_height: number;
}

export interface LOSResultWithProfile extends LOSResult {
  profile?: ElevationSample[];
}

export interface RadialRangeResult {
  bearings: number[];
  ranges: number[];
}

export interface RadialRangeRequest {
  lat: number;
  lon: number;
  alt: number;
  antenna_height?: number;
  max_range_m: number;
  bearings?: number;
  range_steps?: number;
}

export async function fetchElevation(
  lat: number,
  lon: number,
): Promise<ElevationResult> {
  const res = await fetch(`${BASE}/elevation?lat=${lat}&lon=${lon}`);
  return res.json();
}

export async function checkLOS(
  fromLat: number,
  fromLon: number,
  toLat: number,
  toLon: number,
): Promise<LOSResult> {
  const params = new URLSearchParams({
    from_lat: String(fromLat),
    from_lon: String(fromLon),
    to_lat: String(toLat),
    to_lon: String(toLon),
  });
  const res = await fetch(`${BASE}/los?${params}`);
  return res.json();
}

export async function fetchLOSProfile(
  fromLat: number,
  fromLon: number,
  toLat: number,
  toLon: number,
  samples: number = 50,
): Promise<LOSResultWithProfile> {
  const params = new URLSearchParams({
    from_lat: String(fromLat),
    from_lon: String(fromLon),
    to_lat: String(toLat),
    to_lon: String(toLon),
    include_profile: "true",
    samples: String(samples),
  });
  const res = await fetch(`${BASE}/los?${params}`);
  return res.json();
}

export async function fetchRadialRange(
  req: RadialRangeRequest,
): Promise<RadialRangeResult> {
  const res = await fetch(`${BASE}/radial-range`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return res.json();
}
