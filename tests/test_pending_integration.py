"""Requirements awaiting real implementation; no fake endpoint success."""
import pytest


@pytest.mark.skip(reason='Backend/frontend/DEM absent; requirement only, no integration executed')
@pytest.mark.parametrize('scenario', [
    'missing_dem_503', 'dem_read_error', 'route_inside_real_dem',
    'mars_distance_and_projection', 'frontend_post_draw_replace',
    'frontend_network_server_invalid_response_errors',
])
def test_pending_requirement(scenario):
    raise AssertionError('Replace placeholder with implementation-backed assertions before unskipping')
