import pytest
import requests

BASE_URL = 'http://127.0.0.1:5000/distance'


def test_valid_distance():
    data = {
        'lat1': 40.7128,
        'lon1': -74.0060,
        'lat2': 41.8781,
        'lon2': -87.6298
    }
    response = requests.post(BASE_URL, json=data)
    assert response.status_code == 200
    result = response.json()
    assert 'distance_km' in result
    assert isinstance(result['distance_km'], float)


def test_missing_coordinates():
    data = {
        'lat1': 40.7128,
        'lon1': -74.0060
        # missing lat2 and lon2
    }
    response = requests.post(BASE_URL, json=data)
    assert response.status_code == 400
    result = response.json()
    assert 'error' in result
    assert result['error'] == 'Missing coordinates'


def test_empty_payload():
    response = requests.post(BASE_URL, json={})
    assert response.status_code == 400
    result = response.json()
    assert 'error' in result
    assert result['error'] == 'Missing coordinates'
