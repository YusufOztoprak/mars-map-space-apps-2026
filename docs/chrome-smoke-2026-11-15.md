# Independent Chrome smoke test — 15 November 2026

Application: integration branch commit `0be8458`, product baseline main `008cf73`.
URL: http://127.0.0.1:5055/ (README-supported MARS_PORT override).
Real CTX/MOLA available. Actual Windows Google Chrome UI was operated via Computer Use; these are browser observations, not HTTP/Leaflet doubles. This is a targeted smoke test, not exhaustive visual acceptance.

## Executed checks

| Scenario | Result | Observed evidence |
| --- | --- | --- |
| Load 3D application | PASS | Rendered Mars globe; CTX and Mars terrain data ready |
| Enter README coordinates and calculate | PASS | Start 18.44,77.42; end 18.46,77.40; three visible candidate routes |
| Route metrics | PASS | Shortest 1.656 km, max slope 16.1 degrees, 1.22 h; Balanced 1.656 km, max 11.7; Smoother 1.691 km, max 10.3 |
| Select Balanced | PASS | Selected card expanded; orange highlighted route; 1.15 h; comparison displayed |
| Enable slope layer | PASS (visual smoke) | Colored terrain and degree legend appeared; this is not independent pixel-by-pixel scientific validation |
| Clear | PASS | Start/end values, candidate cards and route lines removed; science markers remained |
| Invalid input | PASS | Start `bad` produced 'Enter valid latitude and longitude for both endpoints.' |
| Recovery and same-point request | PASS | Valid input after error returned 0 km / 0 h and same-elevation-cell explanation |
| Missing data disclosure | PASS | Radiation, temperature and dust gaps shown as Missing (0%) |
| Remote imagery | WARNING | Some tiles failed; explicit warning and coarse fallback remained; not complete tile availability |
| 2D Jezero navigation/startup | FAIL | legacy.html remained blank; Chrome blocked Leaflet script due to SRI mismatch |
| 2D point picking/route/reset | BLOCKED | Cannot execute until Leaflet loads |

## Reproducible Windows checkout defect

1. On this Windows checkout, start the current app with MARS_PORT=5055.
2. Open the 3D app and select '2D Jezero'.
3. Observe blank map and inspect Chrome Console.

Console: failed to find a valid digest for frontend/vendor/leaflet/leaflet.js; resource blocked. Then app.js:17 reports `ReferenceError: L is not defined`.

Expected HTML SHA-256 (base64): `20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=`.
Actual checked-out file: `MQS1JlBNDWH9MJmkUh6H9zLMwxdN7FTgjea6i94+Ff8=`.
Git blob and LF-normalized working file both match the expected HTML hash. Therefore Windows CRLF conversion, rather than a different library version, explains this reproduction. Existing .gitattributes preserves PDS bytes only; it does not preserve Leaflet JS bytes.

Owner: frontend/repository configuration. Suggested fix: preserve vendor assets with suitable .gitattributes rules (for example the hashed JS/CSS as `-text`), restore their exact upstream bytes, and verify in a fresh Windows clone. Preserve integrity checking rather than bypass browser security. Integration/test did not edit product files or disable protections. Retest 2D after the owner fixes this.

## Limits

No physical phone test was requested for this run. No actual demo-machine acceptance, network outage injection, exhaustive imagery catalog, every scientific popup, timeout/race stress test or browser-version matrix was completed. Initial window-focus/tool-index issues were recovered using a fresh screenshot and were not recorded as product failures. Screenshots and console evidence were observed in the tool conversation.

Overall: 3D smoke flow passed with a remote-image warning; Windows legacy-2D startup failed. Automated 103 Python/12 flow/6 policy passes do not override this real-browser defect.
