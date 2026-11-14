# Space Apps 2026 — Submission Draft (not submitted)

- **Challenge:** Interplanetary Survival Guide: Martian Map
- **Team name:** Manifest
- **Team members:** Yusuf Öztoprak, Yusuf Tunç, Eren YILMAZ, Emirsultan BOĞATEKİN, Abdullah Demirel
- **Repository:** https://github.com/YusufOztoprak/mars-map-space-apps-2026

## Official project-page fields and rules

The [2026 Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) lists these fields: Project Name; High-Level Project Summary; Link to Project Demo; Link to Final Project; Detailed Project Description; Use of Super Intelligence (SI); NASA Data; Space Agency Partner Data and Other References. The public guide gives no character limits. The account-specific Project page requires login; check for field counters when the team opens it.

- **Demo:** link to a public, no-login video of at most 30 seconds, or a slide deck of at most 7 slides including title and intro slides. Slides and submission text must be in English; a non-English video needs English subtitles. The site does not accept video/document uploads.
- **Final project:** provide a public URL that needs no password, permission, or registration; a website or code repository is acceptable.
- **Images:** JPG, PNG, or GIF uploads up to 10 MB are allowed.
- **Team:** the project page belongs to the registered team. All members must be confirmed for the same Local Event. The demo should show the team name and member names. Confirm the team name against the NASA team page.
- **Submission deadline:** November 15 at 11:59 p.m. in the Local Event time zone; for the Universal Event, use the Team Owner’s local time.

## Copy-ready field draft

### Project Name

**Jezero Safe Route — a layered Marswalk planner**

### High-Level Project Summary

Jezero Safe Route is a web map for planning Marswalks across Jezero Crater. It combines 20 m/pixel CTX elevation data, HiRISE imagery, and Perseverance science sites. Choose a start and destination to calculate a route that avoids modeled slopes above 20° and reports distance, estimated walking time, and maximum slope. A global MOLA hillshade adds planetary context but does not affect routing.

### Link to Project Demo

**TBD:** add the public slide-deck or ≤30-second video URL. Test it in a private browser window before submission.

### Link to Final Project

https://github.com/YusufOztoprak/mars-map-space-apps-2026

### Detailed Project Description

Users select two locations on an interactive map of Jezero Crater. The Flask API reads the USGS 20 m/pixel CTX DEM, derives slope, excludes cells above the 20° prototype limit and no-data cells, then uses a Tobler-based walking cost and weighted A* to return a GeoJSON route with distance, estimated time, and maximum slope. The Leaflet map displays the route over NASA Mars Trek HiRISE imagery, with optional slope-hazard and global MOLA context layers. Five Perseverance waypoints open credited rover images and short science summaries.

The route is a planning aid, not a safety certification. A 20 m DEM cannot resolve small rocks or scarps; 20° and 2.2 km/h are prototype assumptions. The roughly 463 m/pixel MOLA hillshade is visual context only. Requests over 30 km straight-line distance are rejected.

### Use of Super Intelligence (SI)

Claude and Claude Code assisted with backend and frontend implementation, debugging, and tests; Gemini supported literature review; ChatGPT helped structure science-point data, draft summaries and attributions, and check image/DEM metadata. Team members reviewed the output and checked factual claims against NASA/USGS sources. No imagery was AI-generated; mission images and science data are NASA/USGS products.

### NASA Data

| Data | Use | Attribution |
|---|---|---|
| NASA Mars Trek HiRISE Jezero orthomosaic, ~25 cm/pixel | Visual base map | NASA/JPL/University of Arizona · NASA Mars Trek |
| USGS Mars 2020 Science Investigation CTX DEM mosaic, 20 m/pixel | Slope and route calculation | Fred Calef / USGS Astrogeology Science Center; PDS originator |
| NASA Mars Trek MGS MOLA Global Color Hillshade, ~463 m/pixel | Optional global visual context only | NASA/JPL/GSFC · NASA Mars Trek |
| Perseverance waypoint GeoJSON and raw images | Science-site markers and popups | NASA/JPL-Caltech; image-specific credits in `data/science_points.json` |

Full source links and limits: [`data_sources.md`](../data_sources.md).

### Space Agency Partner Data and Other References

No Space Agency Partner datasets were used. Other resources include Leaflet.js (BSD-2-Clause), Python/Flask and geospatial libraries, the NASA Science Lake Salda article, and the public project repository. See [`data_sources.md`](../data_sources.md), [`ai_usage.md`](../ai_usage.md), and the repository for the full source and tool list.

## Lake Salda slide copy

NASA identifies Türkiye’s Lake Salda as the only known lake on Earth with carbonate minerals and delta deposits similar to those at Jezero. Studying Salda’s microbialites and sedimentary processes helps researchers frame questions about Jezero’s ancient lake environment.

Source: [NASA Science — “What a Lake in Turkey Can Tell Us about Mars”](https://science.nasa.gov/blogs/earth-matters/2021/02/17/what-a-lake-in-turkey-can-tell-us-about-mars/).

## Slide outline (maximum 7 slides)

1. Title, team, and challenge.
2. Jezero problem and our live route planner.
3. NASA data layers: HiRISE, CTX DEM, MOLA context, and Perseverance sites.
4. Route method: elevation → slope → walking cost → A*.
5. Demo: choose two points, view route, toggle slope hazards, open a science popup.
6. Lake Salda analogue and Earth relevance.
7. Validation status, limitations, and future Mars-wide work.

## 30-second video alternative

- **0–5 s:** Jezero map — “Plan a Marswalk through Jezero Crater.”
- **5–15 s:** Select endpoints; show the generated route and metrics.
- **15–23 s:** Toggle slope hazards, then open a Perseverance science popup.
- **23–30 s:** “NASA data, live routing, and science along the way.”
