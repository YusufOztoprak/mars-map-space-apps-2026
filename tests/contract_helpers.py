"""Proposed contract checks only; these do not implement or call a backend."""
import math


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_route(payload):
    """Raise ValueError for responses outside the proposed GeoJSON contract."""
    if not isinstance(payload, dict) or payload.get('type') != 'Feature':
        raise ValueError('Expected GeoJSON Feature')
    geometry = payload.get('geometry')
    if not isinstance(geometry, dict) or geometry.get('type') != 'LineString':
        raise ValueError('Expected LineString')
    coordinates = geometry.get('coordinates')
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError('Expected at least two positions')
    for position in coordinates:
        if not isinstance(position, list) or len(position) != 2:
            raise ValueError('Expected [longitude, latitude]')
        lon, lat = position
        if not number(lon) or not number(lat) or not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise ValueError('Invalid position')
    properties = payload.get('properties')
    if not isinstance(properties, dict):
        raise ValueError('Expected properties')
    for key in ('distance_km', 'estimated_time_hours', 'max_slope_deg'):
        value = properties.get(key)
        if not number(value) or value < 0:
            raise ValueError('Invalid ' + key)
    if properties['max_slope_deg'] > 90:
        raise ValueError('Slope exceeds 90 degrees')


def validate_endpoints(payload, start, end, tolerance=1e-6):
    """Fixture check; backend snapping tolerance must be agreed separately."""
    validate_route(payload)
    positions = payload['geometry']['coordinates']
    for actual, expected in ((positions[0], start), (positions[-1], end)):
        if any(abs(a - b) > tolerance for a, b in zip(actual, expected)):
            raise ValueError('Endpoint mismatch')
