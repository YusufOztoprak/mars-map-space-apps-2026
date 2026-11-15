"""DEM (Digital Elevation Model) loading and slope calculation utilities."""
import numpy as np

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


def load_dem(path):
    """Load a real DEM GeoTIFF. Returns (elevation_array, transform, crs, nodata)."""
    if not HAS_RASTERIO:
        raise RuntimeError("rasterio not installed - run: pip install rasterio")
    with rasterio.open(path) as src:
        elevation = src.read(1).astype(np.float64)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
    return elevation, transform, crs, nodata


def generate_synthetic_dem(width=200, height=200, cellsize=25.0, seed=42):
    """
    Generate a fake Jezero-like DEM for local testing before the real
    GeoTIFF is ready. Creates a crater-like bowl plus a few random steep
    bumps, so A* actually has hazards to route around.
    Returns (elevation in meters, cellsize in meters/pixel).
    """
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:height, 0:width]
    cx, cy = width / 2, height / 2
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    elevation = 50 * np.cos(dist / (width / 6))
    elevation += rng.normal(0, 3, size=(height, width))  # sensor noise

    # A few steep "hazard" hills to force the router around them
    for _ in range(5):
        hx, hy = rng.integers(0, width), rng.integers(0, height)
        hr = rng.integers(10, 25)
        hh = rng.integers(30, 80)
        d = np.sqrt((x - hx) ** 2 + (y - hy) ** 2)
        elevation += hh * np.exp(-(d ** 2) / (2 * hr ** 2))

    return elevation.astype(np.float64), cellsize


def compute_slope(elevation, cellsize):
    """
    Compute slope in degrees from an elevation grid using np.gradient.
    cellsize = ground resolution in meters/pixel (e.g. 0.25 for 25cm HiRISE).
    """
    dy, dx = np.gradient(elevation, cellsize)
    slope_radians = np.arctan(np.sqrt(dx ** 2 + dy ** 2))
    return np.degrees(slope_radians)


def terrain_metrics(elevation, cellsize, nodata, horizontal_spacing=None):
    """Return valid elevation, central-difference slope, and a five-cell roughness proxy."""
    valid = np.isfinite(elevation)
    if nodata is not None:
        valid &= elevation != nodata
    heights = np.where(valid, elevation, np.nan).astype(np.float32)
    if horizontal_spacing is None:
        slope = compute_slope(heights, cellsize)
    else:
        dy, dx = np.gradient(heights, cellsize, horizontal_spacing)
        slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    slope[~valid] = np.nan
    roughness = np.full(heights.shape, np.nan, dtype=np.float32)
    cross_mean = (heights[:-2, 1:-1] + heights[2:, 1:-1] +
                  heights[1:-1, :-2] + heights[1:-1, 2:]) / 4
    roughness[1:-1, 1:-1] = np.abs(heights[1:-1, 1:-1] - cross_mean)
    return heights, slope, roughness
