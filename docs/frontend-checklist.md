# Independent frontend verification

## Submission refresh — current root test run

Current main snapshot: `e880bcc36e7f2b7b6a8bf2c9ec3dd3f92bb73583`.
The integration branch was synchronized with main; main's current AI disclosure was preserved.
Root `python -m pytest -v --tb=short`: **54 PASS, 0 FAIL, 7 SKIP** (0.76 s), without source-directory overrides. Six skips are pending requirements; one is the upstream real-DEM module skipped because this checkout has no DEM.
Frontend `node --test tests/frontend-flow.cjs`: **12 PASS, 0 FAIL** (183.566 ms), pinned to the same revision without a source override.
The real-DEM clean-install result below (12 PASS) belongs to earlier revision `b23c168`, not a new real-DEM execution of e880bcc.
After two fetch checks, the announced `backend/tests/test_routing.py` and corner-cutting fix were not present in origin/main e880bcc. Their verification remains pending publication; the team should send the exact commit if it was pushed elsewhere.
The remaining sections document the earlier clean-install rehearsal and its limitations. Chrome/phone acceptance remains pending.


Updated: 14 November 2026 (Europe/Istanbul).
Source under review: main `b23c168fe72958c7e86e56ffdec61897bc6df19c`.
This is integration/test evidence, separate from frontend-team claims in README/AI disclosure.

## Executed application-flow tests

Command: `node --test tests/frontend-flow.cjs`, with `FRONTEND_SNAPSHOT_DIR` pointing to the clean clone. Result: **12 PASS, 0 FAIL**. Unmodified application JavaScript executes in Node; Leaflet, fetch, DOM and viewport APIs are doubles. Two `L.geoJSON` calls are expected because the route has a dark outline and a cyan foreground.

| Test | Status | What it demonstrates |
| --- | --- | --- |
| Click sequence/request/summary/reset | PASS | First click selects start; second POSTs numeric lat/lng/lon; third removes prior markers/route; metric formatting works |
| HTTP 400 | PASS | Error shown, no route drawing calls |
| HTTP 422 | PASS | Error shown, no route drawing calls |
| HTTP 500 | PASS | Error shown, no route drawing calls |
| HTTP 503 | PASS | Error shown, no route drawing calls |
| Network error | PASS | Understandable connection-error message |
| One-position LineString | PASS | Invalid geometry rejected before Leaflet |
| Negative distance | PASS | Marked invalid rather than displayed as a valid number |
| NaN distance | PASS | Marked invalid |
| Infinite distance | PASS | Marked invalid |
| String distance | PASS | Marked invalid |
| Boolean distance | PASS | Marked invalid |

Evidence: [frontend-test-output.txt](frontend-test-output.txt). Invalid metrics may leave valid geometry visible; rejecting the whole route is not required by this acceptance criterion. This is not a complete malformed-response matrix.

## Independent verification matrix

| Feature/claim | Independent check | Current status | Remaining evidence |
| --- | --- | --- | --- |
| Request contract | Execute real request-building code | PASS with doubles | Chrome network trace against real backend |
| Response validation | Inject bad geometry/metrics | PASS with doubles | Real browser error display |
| Draw/reset/summary | Observe Leaflet calls and formatting | PASS with doubles | Actual rendered line, bounds and summary |
| Error handling | Inject HTTP/network errors | PASS with doubles | Stop/restart server during browser session |
| Real CORS | Flask preflight tests | PASS at API level | Browser-origin enforcement |
| CRS/Mars scale | Source inspection | PENDING runtime validation | Known-distance scale check; tile/DEM reference points |
| HiRISE/MOLA tiles | Source configuration present | PENDING | Live images and alignment; URL comments are not independent proof |
| Hazard layer/legend | Files and configuration present | PENDING | Toggle in browser, verify classes and spatial match |
| Science points | Five features/coordinates/required metadata checked previously | PARTIAL | All live popups, image loading and attribution |
| Mobile layout | Responsive code/screenshots present | PENDING | Physical phone, orientation and touch interactions |
| Repeated/overlapping requests | Abort logic present | PENDING | Delayed-response race and timeout tests |

Frontend-team browser/overlay sampling results may be referenced as team evidence, but were not rerun independently here. Chrome access ended when Computer Use could not confidently determine the current browser URL on Windows. This was a tooling stop, not proof of an application failure.

## Chrome and phone checklist

For each item record PASS/FAIL/SKIP, observed result, device/browser version and screenshot:

1. Load from port 8000; confirm no blocking CDN errors and visible tiles.
2. Choose start/end; inspect POST body and real GeoJSON; confirm drawn endpoints.
3. Check distance, time and maximum slope, then select a new route and check cleanup.
4. Toggle hazard overlay and legend; compare route/reference points against the DEM.
5. Open all five science-site popups; verify photos and credits.
6. Request same-cell, out-of-coverage and over-limit routes; check feedback.
7. Simulate backend loss, server error and timeout; confirm recovery without stale drawing.
8. On a physical phone, repeat selection, reset, popup scrolling, overlay toggling and orientation changes.

Phone prerequisite: agree on reachable frontend/API URLs. The current localhost API address, loopback binding and localhost-only CORS do not establish LAN phone support. Owners must approve the serving strategy; integration/test should not silently rewrite their code or network settings.
