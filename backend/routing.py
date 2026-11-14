"""Tobler's Hiking Function cost model + A* pathfinding on a slope-weighted grid."""
import heapq
import numpy as np

SAFETY_THRESHOLD_DEG = 28.0  # slopes steeper than this are impassable for an EVA astronaut
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


def astar(cost_grid, start, goal):
    """Grid A* with Euclidean heuristic. start/goal = (row, col). Returns None if no path exists."""
    height, width = cost_grid.shape
    if cost_grid[start] == np.inf or cost_grid[goal] == np.inf:
        return None

    def heuristic(a, b):
        return np.hypot(a[0] - b[0], a[1] - b[1])

    neighbors = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]

        for dr, dc in neighbors:
            nr, nc = current[0] + dr, current[1] + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            step_cost = cost_grid[nr, nc]
            if step_cost == np.inf:
                continue
            diag = 1.4142 if dr != 0 and dc != 0 else 1.0
            tentative_g = g_score[current] + step_cost * diag
            neighbor = (nr, nc)
            if tentative_g < g_score.get(neighbor, np.inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None