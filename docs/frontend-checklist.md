# Independent frontend verification

## Chrome update — 15 November 2026

[Actual Chrome smoke test](chrome-smoke-2026-11-15.md): 3D loading, three candidate routes, Balanced selection, slope toggle/legend, Clear, invalid input and same-point recovery passed. Some remote tiles failed with an explicit fallback warning. **Legacy 2D startup FAILED on this Windows checkout**: CRLF conversion changes the Leaflet JS bytes, causing SRI rejection and `L is not defined`. This supersedes the generic browser-pending status below for the executed smoke scenarios; 2D retesting and unexecuted scenarios remain pending. Product files were not changed.

Updated 15 November 2026. Product source baseline: main `008cf734fab40d5cad606170b37f6435d60775be`, with integration-only changes on `entegrasyon-test`. No backend/frontend product files were modified.

## Executed automated checks

Current-source 2D flow: **12 PASS** (click sequence/request mapping/reset/summary; HTTP 400/422/500/503; connection error; invalid geometry; negative/NaN/infinite/string/bool metric values). The harness follows the English function names and supplies an explicit port-8000 location context. It uses DOM, Leaflet and HTTP doubles.
Explorer imagery policy: **6 PASS** (far/near appearance, zoom blending, full-view footprint selection, finer regional selection and LOD metadata). Neither suite proves actual canvas/WebGL rendering.

## Independent verification matrix

| Feature | Automated evidence | Browser/device acceptance |
| --- | --- | --- |
| Current-source 2D request/response/reset | 12 flow tests pass with doubles | Pending |
| Explorer image selection | 6 policy tests pass | Pending live tile appearance |
| Real route endpoints/distance/terrain | Current backend and numerical reference tests pass | Pending rendered route comparison |
| CORS and invalid API input | Flask checks pass | Pending actual browser-origin behavior |
| Archived environmental evidence/raster layers | Scientific-data tests pass with real terrain files | Pending legend/popup readability |
| 3D globe, camera, layer toggles | Policy/API coverage only | Pending WebGL walkthrough |
| Physical phone | No physical device evidence | Pending |

## Operator checklist

Record PASS/FAIL/SKIP, device/browser, revision, actual result and screenshots:

1. Open the same-origin app at http://127.0.0.1:5000/; confirm globe and local resources load.
2. Enter README example start 18.44,77.42 and destination 18.46,77.40; compare candidate cards and select each route.
3. Toggle terrain, slope, geology and environmental layers; verify labels, units, data gaps and camera behavior.
4. Check science/rover popups and remote images/credits.
5. Switch to 2D Jezero; select start/end, reset, check metrics and overlay alignment.
6. Exercise same-cell, invalid/out-of-coverage input, server unavailable and retry flows.
7. Repeat on the actual phone; rotate, touch controls, scroll popups and check viewport clipping.
8. Save any mismatch for its frontend/backend/data owner and retest after a fix.

Actual phone and demo-machine access is not assumed. A responsive desktop viewport is not a physical-phone test. Prior browser automation was blocked by URL identification; any new attempt must be recorded separately.
