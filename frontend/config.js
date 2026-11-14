// =====================================================================
// config.js — EVERYTHING that may change lives here. Change the backend
// address, request format and layer settings here without touching other files.
// =====================================================================

// Address of the backend route service. If the server runs on another
// machine/port, change only this line.
const API_URL = "http://localhost:5000/route";

// Give up if the backend does not answer within this many milliseconds (30 s).
const API_TIMEOUT_MS = 30000;

// The ONE function that builds the request body. If the backend format changes,
// fix only this. start/end are Leaflet L.LatLng objects.
// NOTE: fields are sent by name (lat/lng), not by array position, so there is
// no risk of mixing them up with GeoJSON's [longitude, latitude] order.
// Longitude is sent as both "lng" (Leaflet's name) and "lon" (the backend's
// original name): an older backend read only "lon", the current one accepts
// both. This way we never get a 400, whichever backend version is running.
function buildRouteRequest(start, end) {
  return {
    start: { lat: start.lat, lng: start.lng, lon: start.lng },
    end:   { lat: end.lat,   lng: end.lng,   lon: end.lng },
  };
}

// MOLA colour shaded relief (global Mars, 463 m/pixel): wide-area basemap under
// HiRISE. Visual context only; NOT used for slope or routing
// (routes are computed on the 20 m CTX DEM).
// Note: the extension is .jpg (png returns 404); max zoom is 7 (8 → 404). Verified with curl.
// From zoom 8 up, Leaflet scales the z7 tiles.
const MOLA = {
  url: "https://trek.nasa.gov/tiles/Mars/EQ/Mars_MGS_MOLA_ClrShade_merge_global_463m/1.0.0//default/default028mm/{z}/{y}/{x}.jpg",
  // !! The data team will confirm this credit text on the Mars Trek layer page.
  attribution: "MOLA: NASA/JPL/GSFC",
  maxNativeZoom: 7,
};

// The backend's slope limit (backend/routing.py → SAFETY_THRESHOLD_DEG).
// Shown for information in the summary box only; the backend enforces it.
// If the backend value changes, update it here too.
const SLOPE_THRESHOLD_DEG = 20;

// Science points prepared by the data team (GeoJSON FeatureCollection).
// The path is relative to the page: serve the page FROM THE REPO ROOT
// ("python -m http.server 8000" in the repo root → http://localhost:8000/frontend/index.html),
// otherwise ../data cannot be reached. If the file is missing, the map still works.
const SCIENCE_POINTS_URL = "../data/science_points.json";

// Initial map view: Jezero Crater (centre of the HiRISE mosaic).
const MAP_CENTER = [18.45, 77.40]; // Leaflet order: [latitude, longitude]
const MAP_ZOOM = 12;

// NASA Mars Trek HiRISE Jezero orthomosaic (25 cm/pixel).
// DO NOT CHANGE the URL: the double "//" is intentional, order is {z}/{y}/{x} (row/column).
// Verified with curl: z0..z17 exist, z18 and above return 404.
const HIRISE = {
  url: "https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0//default/default028mm/{z}/{y}/{x}.png",
  // Credit: data_sources.md → HiRISE image usage policy (uahirise.org/media/usage.php)
  attribution: "HiRISE: NASA/JPL/University of Arizona · NASA Mars Trek",
  maxNativeZoom: 17, // highest real zoom level on the server
  maxZoom: 19,       // at 18-19 Leaflet scales the z17 tiles
  // Coverage (LowerCorner/UpperCorner in WMTSCapabilities.xml).
  // No tiles are requested outside this box; outside is empty/404 anyway.
  bounds: [
    [18.3067994, 77.2229331], // south-west corner [latitude, longitude]
    [18.669315, 77.583964],   // north-east corner
  ],
};

// Slope hazard map: backend/make_slope_overlay.py writes these two files into
// frontend/ from the SAME slope data the router uses (CTX DEM, 20 m):
//   slope_overlay.png  → coloured semi-transparent image (transparency is in the image)
//   slope_overlay.json → lat/lon bounds of the image + slope limit
// Paths are relative to the page (frontend/index.html). Because the DEM is
// equirectangular, L.imageOverlay places the image correctly.
const SLOPE_OVERLAY = {
  metaUrl: "slope_overlay.json",
  url: "slope_overlay.png",
  showOnStart: false, // off by default; switched on from the layer panel in the demo
  // Legend colours match the colours in make_slope_overlay.py.
  // The limit ({limit}) comes from slope_limit_deg in slope_overlay.json.
  classes: [
    { color: "#facc15", label: "10–15° moderate" },
    { color: "#f97316", label: "15–{limit}° steep" },
    { color: "#dc2626", label: "> {limit}° blocked (route never enters)" },
  ],
};
