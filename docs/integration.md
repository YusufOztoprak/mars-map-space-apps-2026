# Backend Integration Guide — /route

## Overview
Flask REST API that computes a safety-aware walking route between two points in Jezero Crater, Mars, using the USGS Mars 2020 CTX DEM (20 m/pixel).

## Endpoint
`POST /route` — `Content-Type: application/json`

```json
{"start": {"lat": 18.45, "lon": 77.40}, "end": {"lat": 18.46, "lon": 77.42}}
```

- `lat`/`lon` in degrees (planetocentric latitude, east-positive longitude). `lng` is accepted as an alias for `lon`.
- Values must be finite JSON numbers; strings, booleans, NaN and infinity return 400.
- DEM coverage: lon 76.997–78.583 E, lat 17.581–19.290 N (about 89 × 101 km). The map's HiRISE imagery covers a smaller area: lon 77.223–77.584 E, lat 18.307–18.669 N.

### Response 200
```json
{
  "type": "Feature",
  "geometry": {"type": "LineString", "coordinates": [[77.40, 18.45], [77.42, 18.46]]},
  "properties": {"distance_km": 1.451, "estimated_time_hours": 0.95, "max_slope_deg": 9.1}
}
```
- Coordinates are `[longitude, latitude]` (GeoJSON order), always at least two positions. If start and end fall in the same 20 m cell, the position is repeated.
- `max_slope_deg` never exceeds 20.

### Errors
Always JSON: `{"error": "<message>"}` (message text is Turkish).

| Status | Meaning |
|---|---|
| 400 | Missing/malformed body or non-numeric coordinates |
| 422 | Point outside DEM coverage or on a no-data cell, or no route exists under the slope limit |
| 500 | Unexpected server error |

`GET /health` → `{"status": "ok", "grid": [5067, 4456]}`

## How the route is computed
1. **Elevation:** USGS Mars 2020 Science Investigation CTX DEM mosaic, 20 m/pixel, loaded with rasterio. Projection: equirectangular on the Mars 2000 sphere (R = 3,396,190 m, standard parallel 18.4663°, central meridian 0°), read from the GeoTIFF's own CRS. Lat/lon ↔ pixel conversion uses this projection and the file's affine transform.
2. **Slope** per cell from `np.gradient`.
3. **Walking speed** from Tobler's hiking function, scaled to a 2.2 km/h EVA pace. This is an adapted assumption, not a NASA figure. Cost = seconds to cross a cell.
4. **Impassable cells:** slope above 20° or no data. 20° is a conservative prototype parameter, not a NASA safety standard. The 20 m DEM averages out local steepness, so real slopes can be steeper than the DEM shows.
5. **Search:** weighted A* (8-connected, weight 1.2, heuristic scaled to the minimum cell cost). Route cost is guaranteed to be within 20% of optimal; in our tests the difference was about 2%. A 20 km route takes about 2 seconds.

## Slope hazard overlay
`backend/make_slope_overlay.py` writes `frontend/slope_overlay.png` and `frontend/slope_overlay.json` from the same slope grid the router uses: yellow 10–15°, orange 15–20°, red above 20° (the route never enters red cells). Rerun it if the slope limit changes.

## CORS
Allowed origins: `http://localhost:8000`, `http://127.0.0.1:8000`. Add others in `backend/app.py`.

## Running locally
1. Download the DEM (about 90 MB, not in git) to `data/jezero_dem.tif`:
   `curl -L -o data/jezero_dem.tif "https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif"`
   (on Windows PowerShell use `curl.exe`). Expected SHA-256: `BA7F706EA1B5D63A562F28A7DCF7A7F3C79BCE7F048E6974B57E8A33C30D1BA2`.
2. Backend: `cd backend`, `pip install -r requirements.txt`, `python app.py` → `http://localhost:5000`
3. Frontend, from the repo root: `python -m http.server 8000` → `http://localhost:8000/frontend/index.html`
4. Tests: `cd backend`, `python -m pytest tests/ -v`

## Limits
- Not a safety certification: a 20 m DEM cannot resolve boulders or small scarps.
- Walking time is a model estimate, not measured astronaut performance.