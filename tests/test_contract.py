import pytest
from tests.contract_helpers import validate_route, validate_endpoints


def test_synthetic_response(synthetic_route):
    validate_route(synthetic_route)


def test_endpoint_order(synthetic_route):
    validate_endpoints(synthetic_route, [77.5, 18.4], [77.51, 18.41])
    with pytest.raises(ValueError):
        validate_endpoints(synthetic_route, [18.4, 77.5], [18.41, 77.51])


@pytest.mark.parametrize('coordinates', [[], [[0, 0]], [[181, 0], [0, 0]],
    [[0, 91], [0, 0]], [['77', 18], [0, 0]], [[True, 0], [0, 0]],
    [[float('nan'), 0], [0, 0]], [[float('inf'), 0], [0, 0]], [[0], [0, 0]]])
def test_reject_invalid_positions(synthetic_route, coordinates):
    synthetic_route['geometry']['coordinates'] = coordinates
    with pytest.raises(ValueError):
        validate_route(synthetic_route)


@pytest.mark.parametrize('key', ['distance_km', 'estimated_time_hours', 'max_slope_deg'])
@pytest.mark.parametrize('value', [-1, None, '1', True, float('nan'), float('inf')])
def test_reject_invalid_metrics(synthetic_route, key, value):
    synthetic_route['properties'][key] = value
    with pytest.raises(ValueError):
        validate_route(synthetic_route)


@pytest.mark.parametrize('field,value', [('type', 'FeatureCollection'), ('geometry', None), ('properties', {})])
def test_reject_invalid_structure(synthetic_route, field, value):
    synthetic_route[field] = value
    with pytest.raises(ValueError):
        validate_route(synthetic_route)


def test_reject_impossible_slope(synthetic_route):
    synthetic_route['properties']['max_slope_deg'] = 91
    with pytest.raises(ValueError):
        validate_route(synthetic_route)
