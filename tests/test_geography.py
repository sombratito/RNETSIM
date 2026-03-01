"""Tests for geographic calculations — haversine, bearing, interpolation."""

import math

import pytest

from rnetsim.fabric.geography import (
    EARTH_RADIUS_M,
    bearing,
    haversine_distance,
    interpolate_points,
    point_at_distance,
)


class TestHaversine:
    def test_same_point_is_zero(self):
        d = haversine_distance(35.0, -80.0, 35.0, -80.0)
        assert d == pytest.approx(0.0, abs=0.01)

    def test_known_distance_raleigh_to_durham(self):
        """Raleigh (35.7796, -78.6382) to Durham (35.9940, -78.8986)."""
        d = haversine_distance(35.7796, -78.6382, 35.9940, -78.8986)
        # ~30 km
        assert 28_000 < d < 34_000

    def test_antipodal_points(self):
        """Opposite sides of the earth should be ~half circumference."""
        d = haversine_distance(0, 0, 0, 180)
        expected = math.pi * EARTH_RADIUS_M
        assert d == pytest.approx(expected, rel=0.001)

    def test_symmetric(self):
        d1 = haversine_distance(35.0, -80.0, 36.0, -81.0)
        d2 = haversine_distance(36.0, -81.0, 35.0, -80.0)
        assert d1 == pytest.approx(d2, rel=1e-10)


class TestBearing:
    def test_due_north(self):
        b = bearing(35.0, -80.0, 36.0, -80.0)
        assert b == pytest.approx(0.0, abs=1.0)

    def test_due_east(self):
        b = bearing(0.0, 0.0, 0.0, 1.0)
        assert b == pytest.approx(90.0, abs=1.0)

    def test_due_south(self):
        b = bearing(36.0, -80.0, 35.0, -80.0)
        assert b == pytest.approx(180.0, abs=1.0)

    def test_bearing_range_0_360(self):
        b = bearing(0.0, 0.0, 0.0, -1.0)
        assert 0 <= b < 360


class TestPointAtDistance:
    def test_round_trip(self):
        """Move 1km north, should be ~1km away."""
        lat2, lon2 = point_at_distance(35.0, -80.0, 1000, 0)
        d = haversine_distance(35.0, -80.0, lat2, lon2)
        assert d == pytest.approx(1000, rel=0.01)

    def test_east_movement(self):
        lat2, lon2 = point_at_distance(0.0, 0.0, 10000, 90)
        assert lat2 == pytest.approx(0.0, abs=0.01)
        assert lon2 > 0


class TestInterpolatePoints:
    def test_correct_count(self):
        pts = interpolate_points(0, 0, 1, 1, 10)
        assert len(pts) == 10

    def test_endpoints_match(self):
        pts = interpolate_points(35.0, -80.0, 36.0, -81.0, 5)
        assert pts[0] == pytest.approx((35.0, -80.0))
        assert pts[-1] == pytest.approx((36.0, -81.0))

    def test_single_point(self):
        pts = interpolate_points(35.0, -80.0, 36.0, -81.0, 1)
        assert len(pts) == 1
