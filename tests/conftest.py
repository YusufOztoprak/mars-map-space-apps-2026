import pytest


@pytest.fixture
def synthetic_route():
    # Format example only: no DEM, Mars measurement or computed route.
    return {
        'type': 'Feature',
        'geometry': {'type': 'LineString', 'coordinates': [[77.5, 18.4], [77.51, 18.41]]},
        'properties': {'distance_km': 1.5, 'estimated_time_hours': 0.8, 'max_slope_deg': 12.4},
    }
