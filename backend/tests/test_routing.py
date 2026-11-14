"""Unit tests for the A* search on tiny hand-made grids (no DEM needed)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from routing import astar  # noqa: E402

INF = np.inf


def test_no_corner_cutting_between_blocked_cells():
    # The only way from top-left to bottom-right would be a diagonal step
    # squeezing between two blocked cells. That must not count as a path.
    grid = np.array([[1.0, INF],
                     [INF, 1.0]])
    assert astar(grid, (0, 0), (1, 1)) is None


def test_diagonal_allowed_in_open_terrain():
    grid = np.ones((2, 2))
    assert astar(grid, (0, 0), (1, 1)) == [(0, 0), (1, 1)]


def test_route_goes_around_a_wall():
    grid = np.ones((5, 5))
    grid[1:4, 2] = INF  # vertical wall with gaps at the top and bottom rows
    path = astar(grid, (2, 0), (2, 4))
    assert path is not None
    assert all(np.isfinite(grid[cell]) for cell in path)
    assert path[0] == (2, 0) and path[-1] == (2, 4)
