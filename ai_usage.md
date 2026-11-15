# AI Usage Disclosure

NASA Space Apps Challenge 2026 — *Interplanetary Survival Guide: Martian Map*

We used AI tools to speed up research, coding and testing. Every AI-assisted output was reviewed, run and tested by a team member before it was merged. Team members made all design decisions, and all final code and content were checked against primary sources (NASA/USGS data and documentation).

## Tools used

| Tool | Used for |
|---|---|
| Claude (Anthropic) — chat assistant | Planning, backend code, debugging, test design, documentation drafts |
| Claude Code (Anthropic) | Frontend code and browser testing |
| Gemini (Google) | Literature review before the hackathon |
| ChatGPT (OpenAI) | Early challenge planning; GeoJSON structuring, English science summaries, attribution drafting, and image/DEM metadata checks |
| OpenAI Codex | Repository analysis, API contract checks, integration tests, frontend flow tests and test reports |

## Where AI was used

### Research and planning
- **Literature review (Gemini):** candidate landing sites, NASA Mars Trek layers, terrain-hazard models (Tobler's hiking function, A*), web-mapping projections and Earth analogues such as Lake Salda. The team checked the conclusions against the cited sources and dropped suggestions that were too complex for the hackathon.
- **Planning (Claude, ChatGPT):** schedule, role split and scope decisions. Claude also tested the NASA Mars Trek tile service in a live browser to confirm the real tile URL format and the Jezero HiRISE layer ID before we built on it.

### Backend (`backend/`) — Yusuf Öztoprak
Code was drafted with Claude in a chat session, then reviewed, run, tested and integrated by the team. Claude helped with the Flask API structure, the lat/lon ↔ pixel conversion (derived from the DEM file's own CRS), the Tobler cost model, the A* search and its speed-up (benchmarked before adopting), error handling, pytest tests and the slope overlay script. Behavior was verified with automated tests and manual API and browser tests against the real DEM.

### Frontend (`frontend/`) — Yusuf Tunç
`index.html`, `config.js` and `app.js` were written with Claude Code (Claude Opus 5.5): the Leaflet map in EPSG:4326, the click-to-route flow, route-response validation, science-point popups, the slope-hazard layer with its legend, and the route summary box. Yusuf set the requirements, approved each plan before coding and made all commits. Claude ran every test before reporting results:
- HiRISE tiles checked with curl (zoom 0–17 return images, zoom 18 returns 404).
- Backend responses and CORS checked with curl.
- 13 malformed-response cases tested in headless Firefox (Playwright).
- 6,060 route points from the real DEM sampled against the slope overlay; none fell on a >20° cell.

The presentation screenshots are captures of our running app, not AI-generated images.

### Data and content (`data/`, `data_sources.md`) — Eren YILMAZ and Emirsultan BOĞATEKİN
The team compiled five complete Perseverance waypoints into `data/science_points.json`, preserving approximate-coordinate notes, image links and credits, and concise English science summaries. The Brac preview uses a compact 1200-pixel derivative of the NASA Mastcam-Z natural-color panorama; the USGS 20 m/pixel CTX DEM was downloaded outside the repository for backend handoff. `data_sources.md` records NASA/USGS sources and resolution limits, Leaflet BSD-2 and HiRISE credits, the Lake Salda analogy, and the decision to defer global MOLA coverage. ChatGPT helped structure the GeoJSON, draft summaries and attribution, and check Brac image details and CTX metadata; NASA/USGS mission data and imagery were not AI-generated.

### Integration and testing (`tests/`, `docs/`) — Abdullah Demirel
OpenAI Codex assisted Abdullah Demirel with repository analysis, pytest infrastructure, GeoJSON and coordinate validation, Flask API tests, and Node-based frontend flow tests. Tests covered request formatting, CORS, error responses, same-cell routes, invalid geometry and metrics, slope restrictions, and corner-cutting prevention. Abdullah's integration workflow also included a clean-clone installation rehearsal, downloading the real CTX DEM and verifying its SHA-256 checksum. At revision `db4f9f1`, root pytest reported 57 passed and 7 skipped, the real-DEM backend suite passed all 15 tests, and frontend flow tests passed all 12 checks. Findings and retest results were documented in English reports and verification checklists. Snapshot tests used synthetic DEM fixtures, and frontend flow tests used Leaflet and HTTP doubles; independent Chrome, physical-phone and actual demo-machine acceptance remained pending.

### Documentation and presentation — Yusuf Öztoprak and Yusuf Tunç
The README, the integration guide (`docs/integration.md`), the submission text (`docs/submission.md`) and the demo script were drafted with Claude and then edited and fact-checked by the team. All numbers in them (route times, distances, test results) were measured on our running system. Presentation screenshots are captures of the running app, not AI-generated images. The English submission draft, slide outline and demo script were updated with OpenAI Codex. Record the slide authoring tool and any AI use when the final slide deck is prepared.
## What was not AI-generated
- All map imagery, elevation data and rover photos are NASA/USGS data products, credited in `data_sources.md`. We did not generate or alter any imagery with AI.
- Science-point coordinates come from NASA's Perseverance waypoint data, not from AI output.

## Human verification
- Every AI-suggested change ran locally and passed our tests before it was merged.
- Factual claims (data resolution, projection, credits, the Lake Salda analogue) were checked against NASA/USGS pages.
- Known limits are stated openly in the README: the 20° slope limit is a prototype parameter, the walking-speed model is an adapted assumption, and the route is not a safety certification.