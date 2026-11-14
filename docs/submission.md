# Space Apps 2026 — Submission Draft (not submitted)

- **Challenge:** Interplanetary Survival Guide: Martian Map
- **Team name:** Manifesto
- **Team members:** Yusuf Öztoprak, Yusuf Tunç, Eren YILMAZ, Emirsultan BOĞATEKİN, Abdullah Demirel
- **Repository:** https://github.com/YusufOztoprak/mars-map-space-apps-2026

## Project-page fields and rules (from the team-page screenshots)

- **Project Summary** is required, has a **1,500-character** counter, and suggests 50–200 words.
- **Project Name** is shown as “Project Manifesto”; the screenshot does not show a required marker or character limit.
- **Project Demonstration** and **Project** are required public URLs. The demo must be a slide deck of at most 7 slides (including title and introduction) or a video of 30 seconds or less. Both links must work without a password, permission, or registration; use the complete URL.
- **Project Details**, **Use of Super Intelligence (SI)**, and **NASA Data** are required. SI is multi-select; choose applicable tools, or “I did not use SI” if none. NASA Data uses repeatable Link Text / Link URL rows.
- **Space Agency Partner & Other Data** has repeatable Link Text / Link URL rows; no required marker is visible in the screenshot.
- **Project Submission Verification** asks the team to agree to the terms and confirm the work is original. Complete these only after reviewing the final submission.
- No character limits were visible for Project Name, Project Details, or link fields. The team name shown on the page is **Manifesto**.
- The [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) additionally covers submission requirements and the local-event deadline. Do not submit until the team has reviewed the final links and content.

## Copy-ready field draft

### Project Name

**Jezero Safe Route — a layered Marswalk planner**

### Summary (required; max 1,500 characters; suggested 50–200 words)

Jezero Safe Route is a web map for planning Marswalks across Jezero Crater. It combines 20 m/pixel CTX elevation data, HiRISE imagery, and Perseverance science sites. Choose a start and destination to calculate a route that avoids modeled slopes above 20° and reports distance, estimated walking time, and maximum slope. A global MOLA hillshade adds planetary context but does not affect routing.

### Project Demonstration (required)

**TBD:** add the public slide-deck or ≤30-second video URL. Test it in a private browser window before submission.

### Project (required)

https://github.com/YusufOztoprak/mars-map-space-apps-2026

### Project Details (required)

Users select two locations on an interactive map of Jezero Crater. The Flask API reads the USGS 20 m/pixel CTX DEM, derives slope, excludes cells above the 20° prototype limit and no-data cells, then uses a Tobler-based walking cost and weighted A* to return a GeoJSON route with distance, estimated time, and maximum slope. The Leaflet map displays the route over NASA Mars Trek HiRISE imagery, with optional slope-hazard and global MOLA context layers. Five Perseverance waypoints open credited rover images and short science summaries.

The route is a planning aid, not a safety certification. A 20 m DEM cannot resolve small rocks or scarps; 20° and 2.2 km/h are prototype assumptions. The roughly 463 m/pixel MOLA hillshade is visual context only. Requests over 30 km straight-line distance are rejected.

### Use of Super Intelligence (SI) (required; select all that apply)

Select the form option for **Code and data**; do not select “I did not use SI.” The tools assisted with implementation, debugging, tests, literature review, science-point data, summaries, attributions, and metadata checks. The team reviewed the outputs against NASA/USGS sources. No imagery was AI-generated. The form requires code/data assistance to be acknowledged in descriptive text and metadata; this use is also documented in [`ai_usage.md`](../ai_usage.md).

### NASA Data (required; repeatable Link Text / Link URL rows)

- **Link Text:** NASA Mars Trek — Jezero HiRISE orthomosaic (~25 cm/pixel); **Link URL:** https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0/WMTSCapabilities.xml
- **Link Text:** NASA Mars Trek — MGS MOLA Global Color Hillshade (~463 m/pixel); **Link URL:** https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars
- **Link Text:** NASA/JPL — Perseverance M20 waypoint GeoJSON; **Link URL:** https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json
- **Link Text:** NASA Perseverance Raw Images Gallery — Brac; **Link URL:** https://mars.nasa.gov/mars2020/multimedia/raw-images/ZL0_0262_0690210961_535EBY_N0080000ZCAM05068_1100LMJ
- **Link Text:** NASA Perseverance Raw Images Gallery — Hogwallow Flats; **Link URL:** https://mars.nasa.gov/mars2020/multimedia/raw-images/ZR0_0461_0707862611_428EBY_N0260470ZCAM08482_1100LMJ
- **Link Text:** NASA Perseverance Raw Images Gallery — Wildcat Ridge; **Link URL:** https://mars.nasa.gov/mars2020/multimedia/raw-images/NLF_0509_0712140650_691ECM_N0261222NCAM00709_09_095J
- **Link Text:** NASA Perseverance Raw Images Gallery — Yori Pass; **Link URL:** https://mars.nasa.gov/mars2020/multimedia/raw-images/ZR0_0615_0721540472_488EBY_N0301172ZCAM08622_0340LMJ
- **Link Text:** NASA Perseverance Raw Images Gallery — Three Forks Sample Depot; **Link URL:** https://mars.nasa.gov/mars2020/multimedia/raw-images/SIF_0684_0727663715_964EBY_N0321050SRLC07021_0000LMJ
- **Link Text:** NASA Science — Mars rock samples; **Link URL:** https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/
- **Link Text:** NASA Science — Brac Mastcam-Z panorama; **Link URL:** https://science.nasa.gov/resource/mastcam-zs-view-of-the-area-around-brac-in-mars-jezero-crater/
- **Link Text:** NASA Science — Hogwallow Flats Mastcam-Z views; **Link URL:** https://science.nasa.gov/resource/perseverances-mastcam-z-views-hogwallow-flats/
- **Link Text:** NASA Science — Perseverance explores the Jezero delta; **Link URL:** https://science.nasa.gov/resource/perseverance-explores-the-jezero-crater-delta/
- **Link Text:** NASA/JPL — Hazeltop and Bearwallow samples; **Link URL:** https://www.jpl.nasa.gov/videos/meet-the-mars-samples-hazeltop-and-bearwallow-samples-1213/
- **Link Text:** NASA — Perseverance investigates Martian bedrock; **Link URL:** https://www.nasa.gov/missions/mars-2020-perseverance/perseverance-rover/nasas-perseverance-rover-investigates-intriguing-martian-bedrock/
- **Link Text:** NASA Science — Yori Pass context; **Link URL:** https://science.nasa.gov/blog/a-picture-is-worth-a-thousand-words/
- **Link Text:** NASA Science — Three Forks Sample Depot map; **Link URL:** https://science.nasa.gov/resource/perseverances-three-forks-sample-depot-map/
- **Link Text:** NASA Science — Lake Salda and Mars; **Link URL:** https://science.nasa.gov/blogs/earth-matters/2021/02/17/what-a-lake-in-turkey-can-tell-us-about-mars/

Attributions: HiRISE — **NASA/JPL/University of Arizona · NASA Mars Trek**; MOLA — **NASA/JPL/GSFC · NASA Mars Trek**; Perseverance data/images — **NASA/JPL-Caltech**, with image-specific credits in `data/science_points.json`. MOLA is visual context only; route and slope calculations use the CTX DEM.

### Space Agency Partner & Other Data (repeatable Link Text / Link URL rows)

- **Link Text:** USGS Mars 2020 Science Investigation CTX DEM Mosaic (20 m/pixel); **Link URL:** https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- **Link Text:** Leaflet.js (BSD-2-Clause license); **Link URL:** https://github.com/Leaflet/Leaflet/blob/main/LICENSE
- **Link Text:** Backend software dependencies (Flask, Flask-CORS, NumPy, Rasterio, Pillow); **Link URL:** https://github.com/YusufOztoprak/mars-map-space-apps-2026/blob/main/backend/requirements.txt

No Space Agency Partner datasets were used. See [`data_sources.md`](../data_sources.md), [`ai_usage.md`](../ai_usage.md), and the repository for full source, software, and attribution details.

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
