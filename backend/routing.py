"""Tobler's Hiking Function cost model + A* pathfinding on a slope-weighted grid."""
import heapq
import numpy as np
import math

SAFETY_THRESHOLD_DEG = 20.0  # slopes steeper than this are impassable for an EVA astronaut
BASE_SPEED_KMH = 2.2         # estimated EVA walking speed (honesty note: not an official NASA constant)


def tobler_speed_kmh(slope_degrees):
    """Tobler's Hiking Function: W = 6*e^(-3.5*|tan(slope)+0.05|), rescaled to EVA pace."""
    slope_rad = np.radians(slope_degrees)
    raw = 6.0 * np.exp(-3.5 * np.abs(np.tan(slope_rad) + 0.05))
    return raw * (BASE_SPEED_KMH / 6.0)


def build_cost_grid(slope_degrees, cellsize):
    """Convert slope grid to a time-cost grid. Cells over the safety threshold become np.inf (impassable)."""
    speed_kmh = tobler_speed_kmh(slope_degrees)
    speed_ms = speed_kmh * 1000 / 3600
    with np.errstate(divide='ignore'):
        cost = cellsize / speed_ms
    cost[slope_degrees > SAFETY_THRESHOLD_DEG] = np.inf
    cost[~np.isfinite(cost)] = np.inf
    return cost


def astar(cost_grid, start, goal, h_scale=1.0, weight=1.2):
    """Weighted grid A* with a closed set.

    h_scale: minimum per-cell cost (seconds), so the Euclidean heuristic uses
    the same units as the step costs. weight > 1 trades a bounded amount of
    optimality (path cost <= weight * optimal) for a much faster search.
    Returns a list of (row, col) cells, or None if no path exists.
    """
    height, width = cost_grid.shape
    if cost_grid[start] == np.inf or cost_grid[goal] == np.inf:
        return None

    neighbors = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                 (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)]
    goal_r, goal_c = goal
    h_factor = h_scale * weight

    open_set = [(0.0, 0.0, start)]
    came_from = {}
    g_score = {start: 0.0}
    closed = set()

    while open_set:
        _, g_current, current = heapq.heappop(open_set)
        if current in closed:
            continue
        closed.add(current)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]

        r, c = current
        for dr, dc, step in neighbors:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            cell_cost = cost_grid[nr, nc]
            if cell_cost == np.inf:
                continue
            # No corner cutting: a diagonal step is allowed only if both cells
            # it squeezes past are passable, so the path never clips a blocked cell.
            if dr and dc and (cost_grid[r + dr, c] == np.inf or cost_grid[r, c + dc] == np.inf):
                continue
            tentative_g = g_current + cell_cost * step
            neighbor = (nr, nc)
            if tentative_g < g_score.get(neighbor, np.inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + h_factor * math.hypot(nr - goal_r, nc - goal_c)
                heapq.heappush(open_set, (f_score, tentative_g, neighbor))

    return None