"""DEM tile fetcher, elevation service, and LOS calculator.

Fetches Mapzen Terrain-RGB tiles from AWS S3, decodes elevation,
and calculates line-of-sight between node pairs.

Degrades gracefully when tiles are unavailable (Principle 37).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rnetsim.config import TERRAIN_CACHE_DIR

logger = logging.getLogger(__name__)


@dataclass
class ElevationSample:
    """A point along an elevation profile."""

    distance: float  # meters from start
    terrain_elevation: float  # meters above sea level
    los_height: float  # height of LOS line at this point


@dataclass
class LOSResult:
    """Result of a line-of-sight check."""

    clear: bool
    profile: list[ElevationSample]
    obstruction_point: Optional[ElevationSample] = None
    clearance_min: float = 0.0  # meters, negative = obstructed
    degraded: bool = False  # True if elevation data was unavailable


def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to tile coordinates at a given zoom level."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def decode_terrain_rgb(r: int, g: int, b: int) -> float:
    """Decode Mapzen Terrain-RGB pixel to elevation in meters."""
    return (r * 256 + g + b / 256) - 32768


class TerrainService:
    """Elevation data service with tile caching."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or TERRAIN_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._tile_cache: dict[tuple[int, int, int], bytes] = {}

    async def fetch_tile(self, z: int, x: int, y: int) -> Optional[bytes]:
        """Fetch a terrain tile, using cache if available."""
        cache_key = (z, x, y)
        if cache_key in self._tile_cache:
            return self._tile_cache[cache_key]

        # Check disk cache
        cache_path = self.cache_dir / f"{z}/{x}/{y}.png"
        if cache_path.exists():
            data = cache_path.read_bytes()
            self._tile_cache[cache_key] = data
            return data

        # Fetch from Mapzen Terrain Tiles (AWS S3)
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.content
                    # Save to disk cache
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_bytes(data)
                    self._tile_cache[cache_key] = data
                    return data
                else:
                    logger.warning("Terrain tile %s returned %d", url, resp.status_code)
        except Exception as e:
            logger.warning("Failed to fetch terrain tile: %s", e)

        return None

    async def get_elevation(self, lat: float, lon: float, zoom: int = 12) -> float:
        """Get elevation at a point. Returns 0 if data unavailable."""
        x, y = lat_lon_to_tile(lat, lon, zoom)
        tile_data = await self.fetch_tile(zoom, x, y)

        if not tile_data:
            return 0.0

        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(tile_data))
            # Compute pixel position within the tile
            n = 2 ** zoom
            tile_x = (lon + 180.0) / 360.0 * n - x
            lat_rad = math.radians(lat)
            tile_y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n - y

            px = int(tile_x * img.width) % img.width
            py = int(tile_y * img.height) % img.height

            r, g, b = img.getpixel((px, py))[:3]
            return decode_terrain_rgb(r, g, b)
        except ImportError:
            logger.warning("Pillow not installed — terrain elevation unavailable")
            return 0.0
        except Exception as e:
            logger.warning("Error decoding elevation: %s", e)
            return 0.0

    async def get_elevation_profile(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        samples: int = 20,
    ) -> list[float]:
        """Get elevation samples along a great-circle path."""
        elevations = []
        for i in range(samples):
            frac = i / max(samples - 1, 1)
            lat = lat1 + frac * (lat2 - lat1)
            lon = lon1 + frac * (lon2 - lon1)
            elev = await self.get_elevation(lat, lon)
            elevations.append(elev)
        return elevations

    async def check_los(
        self,
        lat1: float,
        lon1: float,
        alt1: float,
        lat2: float,
        lon2: float,
        alt2: float,
        antenna_height: float = 2.0,
        samples: int = 20,
    ) -> LOSResult:
        """Check line-of-sight between two points.

        Samples terrain along the path and checks if any point
        exceeds the straight line between the two endpoints.
        """
        from rnetsim.fabric.geography import haversine_distance

        distance = haversine_distance(lat1, lon1, lat2, lon2)
        elevations = await self.get_elevation_profile(lat1, lon1, lat2, lon2, samples)

        # If all elevations are 0, data is likely unavailable
        if all(e == 0 for e in elevations):
            return LOSResult(
                clear=True,
                profile=[],
                degraded=True,
                clearance_min=float("inf"),
            )

        # Heights at endpoints (terrain + antenna)
        h1 = (elevations[0] if elevations[0] > 0 else alt1) + antenna_height
        h2 = (elevations[-1] if elevations[-1] > 0 else alt2) + antenna_height

        profile = []
        min_clearance = float("inf")
        obstruction = None

        for i in range(samples):
            frac = i / max(samples - 1, 1)
            sample_dist = distance * frac
            terrain_elev = elevations[i]
            los_height = h1 + frac * (h2 - h1)

            clearance = los_height - terrain_elev
            sample = ElevationSample(
                distance=sample_dist,
                terrain_elevation=terrain_elev,
                los_height=los_height,
            )
            profile.append(sample)

            if clearance < min_clearance:
                min_clearance = clearance
                if clearance < 0:
                    obstruction = sample

        return LOSResult(
            clear=min_clearance >= 0,
            profile=profile,
            obstruction_point=obstruction,
            clearance_min=min_clearance,
        )
