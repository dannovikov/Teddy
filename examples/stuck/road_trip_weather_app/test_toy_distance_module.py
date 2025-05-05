import pytest
from toy_distance_module import haversine_distance


def test_distance_zero():
    # Same point should return 0
    assert haversine_distance(0, 0, 0, 0) == pytest.approx(0)


def test_distance_known():
    # Distance between NYC (40.7128° N, 74.0060° W) and Chicago (41.8781° N, 87.6298° W)
    nyc_lat, nyc_lon = 40.7128, -74.0060
    chicago_lat, chicago_lon = 41.8781, -87.6298
    distance = haversine_distance(nyc_lat, nyc_lon, chicago_lat, chicago_lon)
    # Approximate distance should be around 1145 km
    assert 1100 <= distance <= 1200


def test_distance_antipodal():
    # Antipodal points should be approximately Earth's diameter in km
    assert haversine_distance(0, 0, -0, 180) == pytest.approx(20015, rel=0.1)
