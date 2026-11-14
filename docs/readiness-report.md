# Demo readiness report

## Submission refresh — current root test run

Current main snapshot: `e880bcc36e7f2b7b6a8bf2c9ec3dd3f92bb73583`.
The integration branch was synchronized with main; main's current AI disclosure was preserved.
Root `python -m pytest -v --tb=short`: **54 PASS, 0 FAIL, 7 SKIP** (0.76 s), without source-directory overrides. Six skips are pending requirements; one is the upstream real-DEM module skipped because this checkout has no DEM.
Frontend `node --test tests/frontend-flow.cjs`: **12 PASS, 0 FAIL** (183.566 ms), pinned to the same revision without a source override.
The real-DEM clean-install result below (12 PASS) belongs to earlier revision `b23c168`, not a new real-DEM execution of e880bcc.
After two fetch checks, the announced `backend/tests/test_routing.py` and corner-cutting fix were not present in origin/main e880bcc. Their verification remains pending publication; the team should send the exact commit if it was pushed elsewhere.
The remaining sections document the earlier clean-install rehearsal and its limitations. Chrome/phone acceptance remains pending.


Updated: 14 November 2026 (Europe/Istanbul).
Verified revision: `b23c168fe72958c7e86e56ffdec61897bc6df19c`.

## Decision

**Backend and local clean-install checks passed. Final demo acceptance remains pending Chrome and physical-phone checks on the actual demo computer.** This is a rehearsal on a different computer, not the scheduled 21:00 demo-machine sign-off.

## Verified evidence

| Area | Status | Evidence |
| --- | --- | --- |
| Snapshot/contract tests | PASS | 54 passed, 0 failed, 6 skipped |
| Frontend flow logic | PASS with doubles | 12 passed; no browser rendering claim |
| Real CTX DEM backend tests | PASS | 12 passed in clean-clone environment |
| Clean clone and dependencies | PASS | Separate folder/environment; Pillow included |
| DEM download/integrity | PASS | README SHA-256 matched |
| Backend/frontend startup | PASS | Ports 5000/8000 started |
| Actual demo computer | PENDING | Different machine; must repeat setup there |
| Chrome end-to-end demo | BLOCKED in this run | Automation could not identify browser URL safely |
| Physical phone | PENDING | No device walkthrough performed |

Detailed evidence and commands: [test-report.md](test-report.md).

## Resolved findings

The four original API findings are closed at the tested revision: restricted CORS, strict finite JSON-number coordinates, two-position same-cell geometry, and JSON 500 responses. The later same-point 0.02 km bug is also fixed: distance and time are zero. Backend tests now use the current slope threshold and skip explicitly without the real DEM. Pillow, README team names and committed screenshots are present.

## Remaining release risks and owners

| Risk | Next action | Owner |
| --- | --- | --- |
| Demo hardware differs | Repeat README setup and record revision/hash | Integration/test + demo operator |
| Windows Python alias | Verify usable Python/pip before the run | Demo operator |
| Chrome/phone flow unverified | Execute and record the independent checklist | Integration/test + phone operator |
| Phone API address | `localhost:5000` means the phone itself; choose an agreed deployment/proxy strategy and test it | Frontend/backend owners |
| LAN origin rejected | Current CORS allows only localhost/127.0.0.1:8000, not a LAN IP origin | Backend owner |
| Server reachability | Backend currently binds loopback; do not assume phone access | Backend owner/demo operator |
| Overlay/DEM alignment | Independently sample route cells and overlay reference points | Integration/test + data/backend |
| Route quality/performance claims | Save representative benchmark and reference-path comparison evidence | Backend; independent verification by integration/test |
| Missing/corrupt DEM | Test controlled startup failure and clear recovery instructions | Backend + integration/test |

No product code, firewall or access settings were changed to address phone access. A responsive desktop viewport is not a physical-phone result.

## Presentation wording

We can state that clean setup and real-DEM backend tests passed, and that frontend application-flow tests passed with test doubles. We cannot yet claim that this integration run validated the complete Chrome/phone demo, every hazard-overlay cell, or the weighted-A* optimality/performance bounds.

## Next gate

Run the [21:00 checklist](e2e-plan.md) on the actual demo machine, attach Chrome/phone evidence, and update this decision. Keep DEM files out of Git. The latest report and test changes remain local until explicitly committed/pushed; no merge is performed as part of this documentation update.
