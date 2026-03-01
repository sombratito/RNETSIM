"""Terrain elevation, LOS query, and radial range routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from rnetsim.fabric.terrain import TerrainService

router = APIRouter(prefix="/api/terrain", tags=["terrain"])

# Shared terrain service instance
_terrain_service: TerrainService | None = None


def get_terrain_service() -> TerrainService:
    global _terrain_service
    if _terrain_service is None:
        _terrain_service = TerrainService()
    return _terrain_service


@router.get("/elevation")
async def get_elevation(lat: float, lon: float) -> dict:
    """Get terrain elevation at a point."""
    service = get_terrain_service()
    elevation = await service.get_elevation(lat, lon)
    return {"lat": lat, "lon": lon, "elevation": elevation}


@router.get("/los")
async def check_los(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    from_alt: float = 0.0,
    to_alt: float = 0.0,
    include_profile: bool = False,
    samples: int = 20,
) -> dict:
    """Check line-of-sight between two points.

    When include_profile=True, returns the full elevation profile along the path.
    """
    service = get_terrain_service()
    result = await service.check_los(
        from_lat, from_lon, from_alt,
        to_lat, to_lon, to_alt,
        samples=samples,
    )
    response: dict = {
        "clear": result.clear,
        "degraded": result.degraded,
        "clearance_min": result.clearance_min,
        "from": {"lat": from_lat, "lon": from_lon},
        "to": {"lat": to_lat, "lon": to_lon},
    }
    if include_profile:
        response["profile"] = [
            {
                "distance": s.distance,
                "terrain_elevation": s.terrain_elevation,
                "los_height": s.los_height,
            }
            for s in result.profile
        ]
    return response


# ── Radial range computation ─────────────────────────────────────────


class RadialRangeRequest(BaseModel):
    lat: float
    lon: float
    alt: float = 0.0
    antenna_height: float = 2.0
    max_range_m: float = 15000.0
    bearings: int = 64
    range_steps: int = 10


@router.post("/radial-range")
async def compute_radial_range(req: RadialRangeRequest) -> dict:
    """Compute effective RF range per bearing, accounting for terrain.

    For each bearing direction, walks outward from the node in steps,
    checking LOS at each distance. The effective range is the furthest
    distance with clear line-of-sight.
    """
    from rnetsim.fabric.geography import point_at_distance

    service = get_terrain_service()

    bearing_angles = [360.0 * i / req.bearings for i in range(req.bearings)]
    ranges: list[float] = []
    step_size = req.max_range_m / req.range_steps

    for bearing_deg in bearing_angles:
        effective_range = req.max_range_m

        for step in range(1, req.range_steps + 1):
            dist = step * step_size
            target_lat, target_lon = point_at_distance(
                req.lat, req.lon, dist, bearing_deg,
            )
            target_elev = await service.get_elevation(target_lat, target_lon)

            result = await service.check_los(
                req.lat, req.lon, req.alt,
                target_lat, target_lon, target_elev,
                antenna_height=req.antenna_height,
                samples=10,
            )
            if not result.clear and not result.degraded:
                # Terrain blocks at this distance — effective range is previous step
                effective_range = (step - 1) * step_size
                break

        ranges.append(effective_range)

    return {"bearings": bearing_angles, "ranges": ranges}
