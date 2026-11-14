# Space Apps 2026 — Submission Draft

Challenge: **Interplanetary Survival Guide: Martian Map**
Team: TODO (team name, members)
Repository: https://github.com/YusufOztoprak/mars-map-space-apps-2026

> Draft for the Space Apps submission form, the README intro and the slides. Check the form's actual fields and character limits, then trim. Every number here was measured on our running system on 14 Nov 2026.

---

## Project name

**Jezero Safe Route — a layered Marswalk planner**

## High-level summary (short version, ~100 words)

Jezero Safe Route is a web map that helps plan a safe and scientifically rich walk across Jezero Crater on Mars. It layers data from two NASA missions: Mars Reconnaissance Orbiter imagery and elevation, and Perseverance rover waypoints and photos. Click two points and the app computes a walking route in real time from a 20 m elevation model. It avoids slopes steeper than 20° and estimates distance, walking time and the steepest slope on the way. A slope-hazard layer shows why the route bends, and science stops show what an explorer could study along the way.

## Project details

### What it does
- Shows Jezero Crater with 25 cm/pixel HiRISE imagery.
- Lets the user pick a start and an end point; the backend returns a walking route as GeoJSON with distance, estimated walking time and maximum slope.
- Marks five Perseverance science sites (for example Hogwallow Flats and Wildcat Ridge) with rover photos, credits and one-sentence science summaries.
- Adds an optional slope-hazard layer: yellow 10–15°, orange 15–20°, red above 20°. The route never enters red cells.

### How it works
1. **Elevation:** USGS Mars 2020 Science Investigation CTX DEM mosaic, 20 m/pixel (about 89 × 101 km around Jezero). We read its map projection from the file itself (equirectangular, Mars 2000 sphere) and convert between latitude/longitude and DEM pixels.
2. **Slope** for every cell from the elevation grid.
3. **Walking cost:** Tobler's hiking function turns slope into walking speed, scaled to a 2.2 km/h EVA pace. Each cell's cost is the time needed to cross it.
4. **Safety limit:** cells steeper than 20° or without data are impassable.
5. **Search:** weighted A* over the grid. A 20 km route is computed in about 2 seconds. Route cost is guaranteed to be within 20% of the optimum; in our tests the difference was about 2%.
6. **Map:** Leaflet.js in the Mars equirectangular frame (EPSG:4326-style grid), with NASA Mars Trek tiles.

### How we tested it
- Backend unit tests (pytest) for valid routes, malformed input (400), points outside the data (422) and JSON error handling.
- End-to-end browser tests (headless Firefox): route drawing, reset, error messages, science-point popups, layer panel.
- Consistency check: 13 random routes, 6,060 route points — none falls on a cell above the 20° limit, which confirms that the hazard layer and the routing engine are aligned.

### Benefits and impact
- **For Mars exploration:** a quick way to compare walking routes between science targets before a Marswalk, using real orbital terrain data.
- **On Earth:** the same method (elevation model → slope → walking cost → safest path) applies to search-and-rescue planning, mountain hiking and analog-astronaut field missions.
- **Lake Salda, Türkiye:** NASA uses Lake Salda as an Earth analogue for Jezero because both have carbonate-bearing lake and delta deposits. Our team is from Türkiye, and this tool could plan field routes there too.

### Limitations (stated openly)
- A 20 m elevation model cannot see boulders or small scarps; real slopes can be steeper than the model shows. The route is a planning aid, not a safety certification.
- The 20° limit is a conservative prototype parameter, not a NASA standard.
- The 2.2 km/h EVA walking pace is an adapted assumption, not measured astronaut performance.

### Tools and technologies
Python, Flask, NumPy, rasterio, Pillow, pytest · JavaScript, Leaflet.js · Playwright (browser tests) · Git/GitHub

### Future work
- Whole-Mars coarse routes from the global MOLA elevation model, clearly labeled with a data-confidence level.
- A user-adjustable slope limit in the interface.
- Finer slopes from the 1 m HiRISE elevation model.
- Multi-stop routes that visit several science sites in one walk.
- Seasonal and time-of-day temperature estimates (clearly labeled as model estimates, not forecasts).

## NASA data used

| Data | Mission / instrument | Use | Credit |
|---|---|---|---|
| Jezero HiRISE orthomosaic, 25 cm/pixel (NASA Mars Trek WMTS) | MRO / HiRISE | Base map | NASA/JPL/University of Arizona |
| Mars 2020 Science Investigation CTX DEM mosaic, 20 m/pixel | MRO / CTX (USGS Astrogeology, PDS) | Slope, routing, hazard layer | Fred Calef / USGS Astrogeology Science Center |
| Perseverance waypoints (M20 waypoint GeoJSON) | Mars 2020 | Science-site locations | NASA/JPL-Caltech |
| Perseverance raw images and Mastcam-Z panoramas | Mars 2020 / Mastcam-Z, Navcam | Science-site photos | NASA/JPL-Caltech/ASU (Brac: /MSSS) |
| NASA Science articles on Jezero samples and Lake Salda | — | Science summaries, Earth analogue | NASA Science |

Full links and attribution: `data_sources.md` in the repository.

## Space agency partner data
None used. (TODO: confirm before submitting.)

## References
- NASA Mars Trek: https://trek.nasa.gov/mars
- USGS CTX DEM product record: https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- Perseverance raw images: https://mars.nasa.gov/mars2020/multimedia/raw-images/
- Tobler, W. (1993). Three presentations on geographical analysis and modeling (hiking function).
- Leaflet.js (BSD-2-Clause): https://leafletjs.com
- Full list: `data_sources.md`

## Use of AI
We used Claude (Anthropic), Claude Code, Gemini and ChatGPT for research, coding help, testing and drafting documentation. Every AI-assisted output was reviewed, run and tested by a team member before merging, and factual claims were checked against NASA/USGS sources. No imagery was generated with AI. Details by area: `ai_usage.md`.

---

## Slide outline (7 slides)

1. **Title + problem:** "Where can an astronaut walk safely — and what can they study on the way?" One HiRISE image of Jezero.
2. **Our answer:** a layered map + live route computation. Most Mars maps are static layers; ours computes the route when you click.
3. **Data layers:** MRO (HiRISE, CTX DEM) + Mars 2020 (waypoints, photos). Small icons, one line each.
4. **How the route is computed:** DEM → slope → Tobler walking cost → 20° limit → weighted A*. Simple left-to-right diagram.
5. **Demo:** screenshot with the hazard layer on — the route threading between red slopes at the delta front. Distance, time and max slope in the corner.
6. **Validation and honest limits:** tests, 6,060-point consistency check, 2 s for 20 km; then the three limitations.
7. **Impact + future:** Earth uses (search and rescue, analog missions), Lake Salda link, future work list.

## 30-second video script (if a video is required instead of slides)

- 0–5 s: Jezero Crater map. Text: "Planning a safe Marswalk in Jezero Crater."
- 5–15 s: click two points, the route appears with distance, time and max slope.
- 15–22 s: turn on the hazard layer; the route avoids the red slopes at the delta front.
- 22–28 s: open a science-site popup with a Perseverance photo.
- 28–30 s: "Real NASA data. Live routes. Built at Space Apps 2026."