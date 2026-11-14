// =====================================================================
// app.js — The map, picking points by clicking, requesting a route from
// the backend and drawing it. Settings live in config.js.
// =====================================================================

// ---------- 1) Map ----------
// Mars data is NOT Web Mercator; it is on an equirectangular (lat/lon) grid.
// The tile grid of L.CRS.EPSG4326 (zoom 0 = 2x1 tiles, top-left -180,90)
// matches NASA's default028mm grid exactly, so no tms/{-y} is needed.
// Is this a narrow screen such as a phone? (Checked once on page load; same
// breakpoint as @media (max-width: 600px) in the CSS.)
const NARROW_SCREEN = window.matchMedia("(max-width: 600px)").matches;

// Leaflet's EPSG4326 measures distance with the EARTH's radius (6371 km), so the
// scale bar was ~1.88× wrong on Mars. Keep the tile grid, change only the
// radius to Mars (same Mars 2000 sphere as the backend: 3396190 m).
const MARS_CRS = L.extend({}, L.CRS.EPSG4326, { R: 3396190 });

const map = L.map("map", {
  crs: MARS_CRS,
  center: MAP_CENTER,
  zoom: MAP_ZOOM,
  maxZoom: HIRISE.maxZoom,
});

// ---------- 2) Layers ----------
// MOLA basemap (global Mars): so the area outside the HiRISE box is not black.
// zIndex 0 → stays under HiRISE (zIndex 1) even after toggling it in the panel.
const molaLayer = L.tileLayer(MOLA.url, {
  attribution: MOLA.attribution,
  maxNativeZoom: MOLA.maxNativeZoom,
  maxZoom: HIRISE.maxZoom,
  zIndex: 0,
}).addTo(map);

// HiRISE image layer. Thanks to "bounds", no tiles are requested outside coverage.
const hiriseLayer = L.tileLayer(HIRISE.url, {
  attribution: HIRISE.attribution,
  maxNativeZoom: HIRISE.maxNativeZoom,
  maxZoom: HIRISE.maxZoom,
  bounds: HIRISE.bounds,
}).addTo(map);

// Dashed box showing the HiRISE coverage, so the user can see where the
// high-resolution image ends. interactive:false → it does not block clicks;
// clicks go through to the map.
const coverageBox = L.rectangle(HIRISE.bounds, {
  color: "#ffcc00", weight: 1, dashArray: "6 4", fill: false, interactive: false,
}).addTo(map);

// Science points layer: created empty, filled when the data arrives
// (see section 7). Listed in the layer panel even while empty.
const scienceLayer = L.layerGroup().addTo(map);

// Layer on/off control (top right). Kept in a variable so layers loaded later
// (the slope map) can be added with addOverlay.
const layerControl = L.control.layers(null, {
  "MOLA colour relief (global, 463 m)": molaLayer,
  "HiRISE Jezero (25 cm)": hiriseLayer,
  "HiRISE coverage": coverageBox,
  "Science sites (Perseverance)": scienceLayer,
}, { collapsed: NARROW_SCREEN }).addTo(map); // on phones the layer panel collapses to an icon

L.control.scale({ imperial: false }).addTo(map);

// ---------- 2b) Slope hazard map ----------
// Reads the bounds from the JSON first, then stretches the PNG to those bounds.
// If the files are missing the map works normally; the layer is just not listed.
let slopeLayer = null;

// Legend (bottom right): visible only while the slope layer is on.
const SlopeLegend = L.Control.extend({
  onAdd: function () {
    const d = L.DomUtil.create("div", "status-box slope-legend");
    const title = document.createElement("div");
    title.className = "title"; title.textContent = "Slope (data used by the router)";
    d.append(title);
    SLOPE_OVERLAY.classes.forEach((s) => {
      const row = document.createElement("div");
      const swatch = document.createElement("span");
      swatch.className = "swatch"; swatch.style.background = s.color;
      row.append(swatch, document.createTextNode(s.label.replaceAll("{limit}", this.options.limit)));
      d.append(row);
    });
    return d;
  },
});
let slopeLegend = null;
map.on("overlayadd", (e) => { if (e.layer === slopeLayer && slopeLegend) slopeLegend.addTo(map); });
map.on("overlayremove", (e) => { if (e.layer === slopeLayer && slopeLegend) slopeLegend.remove(); });

fetch(SLOPE_OVERLAY.metaUrl)
  .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then((meta) => {
    const limit = meta.slope_limit_deg;
    if (limit !== SLOPE_THRESHOLD_DEG) {
      console.warn(`Slope limit mismatch: overlay ${limit}°, config.js ${SLOPE_THRESHOLD_DEG}°`);
    }
    // interactive:false → clicking on it counts as a map click (route picking still works).
    // className → "pixelated" in CSS: 20 m cells are shown without blurring.
    slopeLayer = L.imageOverlay(SLOPE_OVERLAY.url, meta.bounds, {
      interactive: false, className: "slope-layer",
    });
    slopeLayer.on("error", () => console.warn("Slope image failed to load:", SLOPE_OVERLAY.url));
    // On phones the bottom corners are needed for the route summary; the legend goes top left (under the zoom buttons).
    slopeLegend = new SlopeLegend({ position: NARROW_SCREEN ? "topleft" : "bottomright", limit });
    layerControl.addOverlay(slopeLayer, "Slope hazard (CTX DEM, 20 m)");
    if (SLOPE_OVERLAY.showOnStart) map.addLayer(slopeLayer); // overlayadd → the legend opens too
  })
  .catch((err) => console.warn("Slope layer not found (" + SLOPE_OVERLAY.metaUrl + "):", err.message));

// ---------- 3) Status box (bottom left) ----------
// Shows instructions, the "computing" state and error messages to the user.
const StatusControl = L.Control.extend({
  onAdd: function () {
    this._div = L.DomUtil.create("div", "status-box");
    // Clicking on the box must not count as a map click:
    L.DomEvent.disableClickPropagation(this._div);
    return this._div;
  },
});
const statusControl = new StatusControl({ position: "bottomleft" }).addTo(map);

// kind: "" (normal), "loading" or "error". We use textContent so text coming
// from the server is never interpreted as HTML (security).
function showStatus(text, kind = "") {
  statusControl._div.className = "status-box" + (kind ? " " + kind : "");
  statusControl._div.textContent = text;
  // While computing, the cursor shows "busy" (CSS: .route-computing)
  map.getContainer().classList.toggle("route-computing", kind === "loading");
}

// ---------- 4) Click state ----------
let startPoint = null;     // first clicked point (L.LatLng)
let startMarker = null;
let endMarker = null;
let routeLayer = null;
let activeRequest = null;  // AbortController used to cancel an in-flight fetch

// Clears everything: markers, route and any unfinished request.
function resetRoute() {
  if (activeRequest) { activeRequest.abort(); activeRequest = null; }
  [startMarker, endMarker, routeLayer].forEach((l) => { if (l) map.removeLayer(l); });
  startPoint = startMarker = endMarker = routeLayer = null;
}

// Simple coloured circle marker (no image file needed).
function addMarker(latlng, color, label) {
  return L.circleMarker(latlng, {
    radius: 8, color: "#fff", weight: 2, fillColor: color, fillOpacity: 1,
  }).bindTooltip(label).addTo(map);
}

map.on("click", (e) => {
  if (startPoint === null || endMarker !== null) {
    // 1st click (or 3rd click → reset first): start point
    resetRoute();
    startPoint = e.latlng;
    startMarker = addMarker(e.latlng, "#2e9e44", "Start");
    showStatus("Click to set the end point.");
  } else {
    // 2nd click: end point → request the route
    endMarker = addMarker(e.latlng, "#d33", "End");
    requestRoute(startPoint, e.latlng);
  }
});

// ---------- 5) Requesting a route from the backend ----------
async function requestRoute(start, end) {
  showStatus("Computing route…", "loading");

  const controller = new AbortController();
  activeRequest = controller;
  // Abort the request on timeout; the "timedOut" flag tells it apart from a
  // reset by the user.
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, API_TIMEOUT_MS);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildRouteRequest(start, end)),
      signal: controller.signal,
    });

    // Try to read the body as JSON; if it is malformed, it stays null.
    let data = null;
    try { data = await response.json(); } catch (_) { /* not JSON */ }

    if (!response.ok) {
      // Backend error format: {"error": "<message>"} + 400/422
      const message = data && data.error ? data.error : `Server error (HTTP ${response.status}).`;
      throw new Error(message);
    }
    // Validate the geometry before drawing; throws if it is broken (goes to catch).
    const geometry = extractRouteGeometry(data);
    drawRoute(geometry, (data && data.properties) || {});
  } catch (err) {
    if (err.name === "AbortError" && !timedOut) return; // reset by the user, ignore silently
    let message = err.message;
    if (timedOut) message = "The server did not respond in time.";
    else if (err instanceof TypeError) message = "Could not reach the server.";
    showStatus("Error: " + message + " (Click the map to try again.)", "error");
  } finally {
    clearTimeout(timer);
    if (activeRequest === controller) activeRequest = null;
  }
}

// ---------- 6) Validating the response and drawing the route ----------
// Is it a real, finite number (not NaN/Infinity)?
const isFiniteNumber = (v) => typeof v === "number" && Number.isFinite(v);

// Accepted response: a GeoJSON Feature (the backend's format) or a bare
// LineString. The geometry must be a LineString with at least 2 valid
// [longitude, latitude] points. Otherwise it throws; the route is NOT drawn.
function extractRouteGeometry(data) {
  const invalid = new Error("The server sent an invalid route.");
  if (!data || typeof data !== "object") throw invalid;
  const g = data.type === "Feature" ? data.geometry : data;
  if (!g || g.type !== "LineString" || !Array.isArray(g.coordinates)) throw invalid;
  if (g.coordinates.length < 2) throw invalid; // a single point is not a line
  // GeoJSON order is [longitude, latitude]: c[0] longitude (−180…180), c[1] latitude (−90…90).
  const isValidPoint = (c) => Array.isArray(c) && c.length >= 2 &&
    isFiniteNumber(c[0]) && isFiniteNumber(c[1]) &&
    Math.abs(c[0]) <= 180 && Math.abs(c[1]) <= 90;
  if (!g.coordinates.every(isValidPoint)) throw invalid;
  return g;
}

// L.geoJSON converts GeoJSON's [longitude, latitude] order to Leaflet's
// [latitude, longitude] itself. Only validated geometry reaches this point.
function drawRoute(geometry, properties) {
  // Two-layer line: a dark, thick "casing" underneath and a cyan line on top,
  // so the route stands out on the yellow/orange slope layer and on light
  // terrain (even on a projector).
  routeLayer = L.featureGroup([
    L.geoJSON(geometry, { style: { color: "#002b36", weight: 8, opacity: 0.7 } }),
    L.geoJSON(geometry, { style: { color: "#00e5ff", weight: 4.5, opacity: 1 } }),
  ]).addTo(map);

  const m = routeMetrics(properties);
  routeLayer.bindPopup(`Distance: ${m.distance} · Est. walking time: ${m.time} · Max. slope: ${m.slope}`);
  showRouteSummary(m);
  // maxZoom: for a very short route (e.g. start and end in the same DEM cell,
  // the backend returns a line of 2 identical points) the map must not jump to max zoom.
  map.fitBounds(routeLayer.getBounds(), { padding: [40, 40], maxZoom: 16 });
}

// Turns the backend's properties into readable text.
// Field missing → "—". Field present but not a finite, non-negative number → "invalid"
// (we never show a wrong number, e.g. a negative distance, to the user).
function routeMetrics(p) {
  const text = (key, format) => {
    const v = p[key];
    if (v === undefined || v === null) return "—";
    if (!isFiniteNumber(v) || v < 0) {
      console.warn(`Invalid route metric ${key}:`, v);
      return "invalid";
    }
    return format(v);
  };
  const fmt = (v, digits) => v.toLocaleString("en-US", { maximumFractionDigits: digits });
  // Turns hours into "1 h 43 min" (easier to read than 1.72 hours).
  const hoursToText = (hours) => {
    const minutes = Math.round(hours * 60);
    return minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)} h ${minutes % 60} min`;
  };
  return {
    distance: text("distance_km", (v) => fmt(v, 2) + " km"),
    time: text("estimated_time_hours", hoursToText),
    slope: text("max_slope_deg", (v) => fmt(v, 1) + "°"),
  };
}

// Turns the bottom-left box into the route summary: title + 3 metrics + hint.
// Built with the DOM (textContent); nothing from the server is interpreted as HTML.
function showRouteSummary(m) {
  const d = statusControl._div;
  d.className = "status-box route-summary";
  const row = (label, value, note) => {
    const s = document.createElement("div");
    s.className = "metric";
    const e = document.createElement("span"); e.className = "label"; e.textContent = label;
    const v = document.createElement("b"); v.textContent = value;
    s.append(e, v);
    if (note) { const n = document.createElement("span"); n.className = "note"; n.textContent = note; s.append(n); }
    return s;
  };
  const title = document.createElement("div");
  title.className = "title"; title.textContent = "Safe walking route";
  const hint = document.createElement("div");
  hint.className = "hint"; hint.textContent = "Click the map to start a new route.";
  d.replaceChildren(
    title,
    row("Distance", m.distance),
    row("Est. walking time", m.time, "Tobler hiking model"),
    row("Max. slope", m.slope, `limit: ${SLOPE_THRESHOLD_DEG}°`),
    hint,
  );
}

// ---------- 7) Science points ----------
// The popup content is built with the DOM (not innerHTML): text from the file
// is never interpreted as HTML, so broken or malicious content cannot affect the page.
function el(tag, text, props = {}) {
  const e = document.createElement(tag);
  if (text) e.textContent = text;
  Object.assign(e, props);
  return e;
}

function sciencePopup(p) {
  const box = el("div", "", { className: "science-popup" });
  box.append(el("h3", p.name || "Unnamed site"));
  if (p.image_preview_url) {
    // loading="lazy": the image is downloaded only when the popup opens. Its space is
    // reserved in CSS with a fixed aspect ratio, so the popup has its final size when it
    // opens and Leaflet pans the map correctly (the image does not grow the popup later).
    box.append(el("img", "", { src: p.image_preview_url, alt: p.image_caption || "", loading: "lazy" }));
    const caption = [p.image_caption, p.image_credit].filter(Boolean).join(" · ");
    if (caption) box.append(el("div", caption, { className: "small" }));
  }
  if (p.science_summary) box.append(el("p", p.science_summary));
  if (p.coordinate_accuracy) box.append(el("div", "Location accuracy: " + p.coordinate_accuracy, { className: "small" }));
  if (p.image_gallery_url) {
    box.append(el("a", "Open raw image at NASA ↗", { href: p.image_gallery_url, target: "_blank", rel: "noopener" }));
  }
  return box;
}

async function loadSciencePoints() {
  try {
    const response = await fetch(SCIENCE_POINTS_URL);
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    L.geoJSON(data, {
      // Draw each GeoJSON point as an orange circle.
      pointToLayer: (_, latlng) => L.circleMarker(latlng, {
        radius: 7, color: "#000", weight: 1, fillColor: "#ff9f1c", fillOpacity: 0.95,
        // Clicking a point must not count as a map click (otherwise it would become a route start).
        bubblingMouseEvents: false,
      }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(f.properties.name || "");
        layer.bindPopup(() => sciencePopup(f.properties), { maxWidth: 300, minWidth: 260 });
      },
    }).eachLayer((l) => scienceLayer.addLayer(l));
  } catch (err) {
    // Science points are an extra: if they fail to load, route planning still works.
    console.warn("Science points failed to load (" + SCIENCE_POINTS_URL + "):", err.message);
  }
}
loadSciencePoints();

showStatus("Click the map to set a start point.");
