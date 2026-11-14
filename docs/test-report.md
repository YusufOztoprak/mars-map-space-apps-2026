# Integration and test report

## Submission refresh — current root test run

Current main snapshot: `e880bcc36e7f2b7b6a8bf2c9ec3dd3f92bb73583`.
The integration branch was synchronized with main; main's current AI disclosure was preserved.
Root `python -m pytest -v --tb=short`: **54 PASS, 0 FAIL, 7 SKIP** (0.76 s), without source-directory overrides. Six skips are pending requirements; one is the upstream real-DEM module skipped because this checkout has no DEM.
Frontend `node --test tests/frontend-flow.cjs`: **12 PASS, 0 FAIL** (183.566 ms), pinned to the same revision without a source override.
The real-DEM clean-install result below (12 PASS) belongs to earlier revision `b23c168`, not a new real-DEM execution of e880bcc.
After two fetch checks, the announced `backend/tests/test_routing.py` and corner-cutting fix were not present in origin/main e880bcc. Their verification remains pending publication; the team should send the exact commit if it was pushed elsewhere.
The remaining sections document the earlier clean-install rehearsal and its limitations. Chrome/phone acceptance remains pending.


Updated: 14 November 2026 (Europe/Istanbul).
Tested main revision: `b23c168fe72958c7e86e56ffdec61897bc6df19c`.
Working branch: `entegrasyon-test`. Product source files were not modified.
This report supersedes earlier revision-specific findings; it is not a claim that every later main revision has been tested.

## Latest results

| Suite | PASS | FAIL | SKIP | Evidence |
| --- | ---: | ---: | ---: | --- |
| Integration/contract pytest suite | 54 | 0 | 6 | [Full output](backend-test-output.txt) |
| Frontend application-flow tests (Node) | 12 | 0 | 0 | [Full output](frontend-test-output.txt) |
| Upstream backend tests with the real CTX DEM | 12 | 0 | 0 | [Full output](real-dem-test-output.txt) |

These are separate executions with overlapping coverage, not 78 unique acceptance criteria.
Integration pytest took 0.91 seconds, Node tests 138 ms, and the real-DEM backend suite 3.27 seconds. These are suite durations, not route-performance benchmarks.

## Methods and reproduction

The snapshot fixture reads the pinned backend revision, imports the real Flask application, and replaces only `dem_utils.load_dem` before import with a flat 200 x 200 synthetic grid and a 20 m affine transform. Real routing, slope and coordinate-conversion code runs; this suite does not verify actual DEM loading.

For a downloaded source snapshot, `BACKEND_SNAPSHOT_DIR` may point to its backend folder. The caller must record and verify its source revision. The latest execution used the clean clone at `C:/Users/Abdullah/Desktop/nasa/dry-run-2026-11-14`.

```powershell
# From the integration working checkout, using its Python environment:
$env:BACKEND_SNAPSHOT_DIR = 'C:\Users\Abdullah\Desktop\nasa\dry-run-2026-11-14\backend'
.venv\Scripts\python.exe -m pytest -v --tb=short
$env:FRONTEND_SNAPSHOT_DIR = 'C:\Users\Abdullah\Desktop\nasa\dry-run-2026-11-14\frontend'
node --test tests/frontend-flow.cjs
# Remove these overrides to use the Git revisions pinned in each test file.
```

Node tests execute the unmodified frontend JavaScript with HTTP, Leaflet, DOM and viewport doubles. They verify application logic, not browser rendering, network CORS enforcement or mobile layout. The frontend source override was used for the same clean-clone revision.

The upstream backend suite ran in the clean clone's separate Python environment, without the synthetic loader patch:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -v --tb=short
```

## Verified fixes and behavior

| Check | Result | Verification scope |
| --- | --- | --- |
| Valid route and GeoJSON contract | PASS | Synthetic snapshot; upstream real-DEM route tests |
| Invalid/missing coordinates | PASS | Invalid types, strings, booleans and non-finite values checked in snapshot tests |
| Allowed/disallowed CORS origins | PASS | Flask preflight responses; localhost:8000 allowed, arbitrary origin rejected |
| Same-cell geometry | PASS | Two-coordinate LineString |
| Identical-point distance and time | PASS | Both zero; earlier 0.02 km regression resolved |
| Unexpected calculation error | PASS | Injected error returns JSON HTTP 500 |
| 20-degree threshold | PASS | 20 degrees traversable; 20.1 degrees blocked in synthetic grid |
| Alternate path/no path | PASS | Synthetic obstacle grid |
| Real DEM loading and route endpoints | PASS | Clean-clone upstream tests |
| Mars one-degree surface distance | PASS | Upstream analytic-distance check |
| Request limit | PASS | Upstream test lowers configured limit and checks 422; not a 30 km benchmark |

The old 28-degree assertion, missing Pillow dependency, missing team list and README screenshot placeholder were corrected in this revision. The referenced screenshot file exists in the clone. Older failure outputs and the general review describe earlier revisions and must not be treated as current results.

## Clean installation evidence

- Clean clone: `C:/Users/Abdullah/Desktop/nasa/dry-run-2026-11-14`.
- Separate environment: Python 3.12.14; backend requirements installed successfully, including Pillow.
- DEM downloaded from the README's USGS URL: 90,345,300 bytes.
- SHA-256: `BA7F706EA1B5D63A562F28A7DCF7A7F3C79BCE7F048E6974B57E8A33C30D1BA2`, matching README.
- Actual backend and static frontend servers started on ports 5000 and 8000.
- Windows `python` resolves to an unusable Store alias here; the bundled Python executable was used to create the environment. This machine-specific setup deviation must be checked on the demo computer.

## Pending checks

Six pytest requirements remain skipped: missing DEM, DEM read error, full route coverage within the real DEM, independent Mars/projection verification, real browser draw/reset flow, and browser error handling. Some have partial coverage elsewhere; the placeholders themselves were not executed and remain SKIP.

Windows Chrome automation stopped because the tool could not reliably determine the current browser URL for policy enforcement. No successful Chrome or physical-phone walkthrough is claimed. This computer is not the demo computer, as confirmed by the user.

Independent frontend verification is detailed in [frontend-checklist.md](frontend-checklist.md). See [e2e-plan.md](e2e-plan.md) for the 21:00 demo-machine handoff. Real overlay alignment, all-route NoData avoidance, mobile interactions, and weighted-A* performance/optimality claims remain unverified by this integration workflow.
