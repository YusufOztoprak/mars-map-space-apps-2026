# AI Usage Disclosure

NASA Space Apps Challenge 2026 — *Interplanetary Survival Guide: Martian Map*

We used AI tools to speed up research, coding and testing. Every AI-assisted output was reviewed, run and tested by a team member before it was merged. Team members made all design decisions, and all final code and content were checked against primary sources (NASA/USGS data and documentation).

## Tools used

| Tool | Used for |
|---|---|
| Claude (Anthropic) — chat assistant | Planning, backend code, debugging, test design, documentation drafts |
| Claude Code (Anthropic) | Frontend code and browser testing |
| Gemini (Google) | Literature review before the hackathon |
| ChatGPT (OpenAI) | Early hackathon planning before the challenge was chosen |
| TODO: Data/Content tool | TODO |
| TODO: Integration/Test tool | TODO |

## Where AI was used

### Research and planning
- **Literature review (Gemini):** candidate landing sites, NASA Mars Trek layers, terrain-hazard models (Tobler's hiking function, A*), web-mapping projections and Earth analogues such as Lake Salda. The team checked the conclusions against the cited sources and dropped suggestions that were too complex for the hackathon.
- **Planning (Claude, ChatGPT):** schedule, role split and scope decisions. Claude also tested the NASA Mars Trek tile service in a live browser to confirm the real tile URL format and the Jezero HiRISE layer ID before we built on it.

### Backend (`backend/`) — Yusuf Öztoprak
Code was drafted with Claude in a chat session, then reviewed, run, tested and integrated by the team. Claude helped with the Flask API structure, the lat/lon ↔ pixel conversion (derived from the DEM file's own CRS), the Tobler cost model, the A* search and its speed-up (benchmarked before adopting), error handling, pytest tests and the slope overlay script. Behavior was verified with automated tests and manual API and browser tests against the real DEM.

### Frontend (`frontend/`) — TODO: name
`index.html`, `config.js` and `app.js` were written together with Claude Code. Direction, requirements and approvals came from the team member. Testing: HiRISE tiles checked with curl (zoom 0–17 return images, zoom 18 returns 404); backend 200/400/422 responses and CORS checked with curl; end-to-end tests in headless Firefox (Playwright) covered route drawing, reset, error messages, science-point popups and the layer panel.

### Data and content (`data/`, `data_sources.md`) — TODO: name
TODO: which tool, and for what (finding Perseverance waypoints and images, writing science summaries, checking attributions).

### Integration and testing (`tests/`, `docs/`) — TODO: name
TODO: which tool, and for what (test design, contract checks, reports).

### Documentation and presentation — TODO: name
TODO: which tool, and for what (README, slides, video script).

## What was not AI-generated
- All map imagery, elevation data and rover photos are NASA/USGS data products, credited in `data_sources.md`. We did not generate or alter any imagery with AI.
- Science-point coordinates come from NASA's Perseverance waypoint data, not from AI output.

## Human verification
- Every AI-suggested change ran locally and passed our tests before it was merged.
- Factual claims (data resolution, projection, credits, the Lake Salda analogue) were checked against NASA/USGS pages.
- Known limits are stated openly in the README: the 20° slope limit is a prototype parameter, the walking-speed model is an adapted assumption, and the route is not a safety certification.