# End-to-end verification and 21:00 dry-run plan

## Submission refresh — current root test run

Current main snapshot: `e880bcc36e7f2b7b6a8bf2c9ec3dd3f92bb73583`.
The integration branch was synchronized with main; main's current AI disclosure was preserved.
Root `python -m pytest -v --tb=short`: **54 PASS, 0 FAIL, 7 SKIP** (0.76 s), without source-directory overrides. Six skips are pending requirements; one is the upstream real-DEM module skipped because this checkout has no DEM.
Frontend `node --test tests/frontend-flow.cjs`: **12 PASS, 0 FAIL** (183.566 ms), pinned to the same revision without a source override.
The real-DEM clean-install result below (12 PASS) belongs to earlier revision `b23c168`, not a new real-DEM execution of e880bcc.
After two fetch checks, the announced `backend/tests/test_routing.py` and corner-cutting fix were not present in origin/main e880bcc. Their verification remains pending publication; the team should send the exact commit if it was pushed elsewhere.
The remaining sections document the earlier clean-install rehearsal and its limitations. Chrome/phone acceptance remains pending.


Date: 14 November 2026; scheduled rehearsal: **21:00 Europe/Istanbul**.
Reference revision already rehearsed locally: `b23c168fe72958c7e86e56ffdec61897bc6df19c`.
The user confirmed that the actual demo computer is a different machine. Local preparation is complete at API/setup level; the actual-machine and phone walkthrough remains pending. This document is a runbook, not a claim that a future run has executed or been scheduled automatically.

## Completed local preparation

Clean clone into `C:/Users/Abdullah/Desktop/nasa/dry-run-2026-11-14`; separate virtual environment; README backend dependencies installed; USGS DEM downloaded and hash matched. The real-DEM backend suite passed all 12 tests. Snapshot tests passed 54 with 6 skips; frontend flow tests passed 12 with doubles. Backend/static servers started on ports 5000/8000. Chrome automation stopped at URL identification; no browser walkthrough completed.

## Before 21:00 on the actual demo computer

1. Confirm the operator, Chrome version, physical phone, network and presentation display.
2. Clone main into a new empty folder; record the exact commit. If it differs from the tested revision, rerun tests rather than inheriting old PASS results.
3. Verify Python 3.10+ and curl. On Windows, check that `python` is not an unusable Store alias. Create/activate an isolated environment and follow README's dependency commands.
4. Download `data/jezero_dem.tif` using the README USGS URL. Expected SHA-256: `BA7F706EA1B5D63A562F28A7DCF7A7F3C79BCE7F048E6974B57E8A33C30D1BA2`. Keep the file out of Git.
5. Run `python -m pytest backend/tests -v` from the repository root and record every outcome.
6. Start backend as documented, then the static frontend on port 8000. Open `http://localhost:8000/frontend/index.html` in Chrome.
7. Agree with frontend/backend owners how the phone reaches the app. A phone's localhost is not the demo PC. Current loopback binding and CORS do not permit arbitrary LAN hosting; resolve and test this before the run.
8. Start a log of elapsed time, setup deviations, errors, owner and fix/retest result. Do not hide a step that required help.

## Acceptance scenarios

The statuses below describe complete browser end-to-end execution, not component-test results. All remain PENDING until run on the target device.

| ID | Scenario | Acceptance criterion | Current component evidence |
| --- | --- | --- | --- |
| E01 | Short real-terrain route | HTTP 200, valid geometry and matching rendered route | Real-DEM backend route PASS |
| E02 | Longer in-range route | Correct endpoints/coverage; measured latency recorded | No independent long-route benchmark |
| E03 | Detour around steep terrain | No above-20-degree/NoData cells; visible alignment | Synthetic obstacle test PASS; real overlay pending |
| E04 | No traversable route | Clear error, no misleading straight line | Synthetic no-path and mocked frontend error PASS |
| E05 | Outside DEM | 422 and usable map afterward | Real-DEM API rejection PASS |
| E06 | Identical point/cell | Two positions, zero distance/time, usable display | Real-DEM/backend regression PASS |
| E07 | Boundaries/NoData | No index overflow or invalid-cell traversal | Full independent sampling pending |
| E08 | Backend unavailable/error | Understandable message and successful retry | Mock flow/JSON-500 component checks PASS |
| E09 | Missing/corrupt DEM | Controlled startup failure and clear recovery | Pending explicit negative setup test |
| E10 | Repeated requests | Only latest selection shown; old route removed | Reset logic PASS with doubles; race pending |
| E11 | Tiles, science points, overlay | Visible, attributed, aligned and interactive | Assets/configuration present; browser check pending |
| E12 | Metrics and route quality | Independent Mars/DEM checks, documented assumptions | Analytic Mars distance test PASS; route sampling pending |
| E13 | Over-distance request | 422 returned promptly with clear message | Backend configured-limit test PASS |
| E14 | Physical-phone walkthrough | Touch selection, reset, popups, layers and orientation work | Pending device and reachable serving strategy |

For E03/E04, choose terrain supported by actual DEM inspection. If unavailable, mark SKIP with the reason; do not substitute a synthetic result for real-terrain acceptance. The slope limit is 20 degrees, a prototype parameter, not a NASA safety standard.

## Evidence and timing

Record scenario ID, date/time, operator, device/browser, source commit, DEM hash, coordinates, request/response/status, elapsed time and screenshots. Establish snap tolerance from the DEM resolution before checking endpoints. Do not use the same backend statistic function as an independent reference. Route-performance and weighted-A* bound claims need separate benchmark/reference-path evidence; suite duration is not route latency.

## Completion and handoff

Integration/test owns result collection and retesting; backend/frontend/data owners fix their respective implementation issues. Demo operator/phone operator performs steps that require the actual hardware. Final sign-off requires evidence from Chrome and a physical phone, or an explicit documented device limitation agreed by the team. Update test-report.md, readiness-report.md and frontend-checklist.md after the run. Do not mark this stage complete solely because component tests passed.
