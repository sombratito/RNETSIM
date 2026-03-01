"""Geographic calculations — distance, bearing, great-circle math.

Pure functions, no external dependencies.
"""

import math

EARTH_RADIUS_M = 6_371_000  # meters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in meters."""
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate initial bearing from point 1 to point 2 in degrees (0-360)."""
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlon = lon2_r - lon1_r

    x = math.sin(dlon) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(
        dlon
    )

    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def point_at_distance(
    lat: float, lon: float, distance_m: float, bearing_deg: float
) -> tuple[float, float]:
    """Calculate destination point given start, distance (m), and bearing (deg)."""
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    brng_r = math.radians(bearing_deg)

    d_over_r = distance_m / EARTH_RADIUS_M

    lat2 = math.asin(
        math.sin(lat_r) * math.cos(d_over_r)
        + math.cos(lat_r) * math.sin(d_over_r) * math.cos(brng_r)
    )
    lon2 = lon_r + math.atan2(
        math.sin(brng_r) * math.sin(d_over_r) * math.cos(lat_r),
        math.cos(d_over_r) - math.sin(lat_r) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


def interpolate_points(
    lat1: float, lon1: float, lat2: float, lon2: float, count: int
) -> list[tuple[float, float]]:
    """Return evenly spaced points along the great-circle path."""
    points = []
    for i in range(count):
        fraction = i / max(count - 1, 1)
        lat = lat1 + fraction * (lat2 - lat1)
        lon = lon1 + fraction * (lon2 - lon1)
        points.append((lat, lon))
    return points
