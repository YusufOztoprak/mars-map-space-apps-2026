# End-to-end acceptance runbook

Updated 15 November 2026. Product source baseline: main `008cf734fab40d5cad606170b37f6435d60775be`, with integration-only changes on `entegrasyon-test`. No backend/frontend product files were modified.

## Preparation already verified

Clean rehearsal clone, independent Python environment, real CTX/MOLA hashes and automated tests are verified. Current integrated test run: 103 Python PASS, 12 flow PASS, 6 policy PASS. This is not the actual demo-machine/phone sign-off. The previously planned 14 November 21:00 session has no execution evidence here; this document does not claim it occurred.

## Target-machine execution

1. Demo operator clones current main into a clean folder and records the commit. Install Python/backend requirements following current README.
2. Download both CTX and MOLA, verify README SHA-256 values, and keep them out of Git.
3. Run root pytest plus the two Node suites; record all failures/skips. Different commits require new results.
4. Start `python backend/app.py`; open http://127.0.0.1:5000/. If occupied, agree on MARS_PORT and record the actual URL.
5. Follow the [frontend checklist](frontend-checklist.md) in Chrome; capture globe, candidate routes, layer controls, gaps, metrics and science popups.
6. Perform the same acceptance on the actual physical phone using an agreed reachable URL. Loopback-only defaults do not establish LAN availability.
7. Record errors, setup deviations, time spent, owner, fix and retest evidence. Frontend/backend/data owners fix their code; integration/test records and verifies.

## Required scenarios

| ID | Scenario | Component evidence | Remaining end-to-end evidence |
| --- | --- | --- | --- |
| E01 | Jezero route and endpoints | Real-terrain API/numerical tests pass | Rendered line and cards |
| E02 | Global and polar routes | Current real-MOLA tests pass | Globe interaction and camera |
| E03 | Steep cells/NoData/corner cutting | Algorithm and real-route checks pass | Visual overlay agreement |
| E04 | Missing/corrupt DEM | Integration JSON-503 tests pass | Operator recovery instructions |
| E05 | Identical point | Zero distance/time tests pass | Stable viewport and summary |
| E06 | Invalid request/no path | API and mocked flow checks pass | Usable browser error/retry |
| E07 | Successive/overlapping requests | Reset logic covered with doubles | Race/timeout in actual browser |
| E08 | Scientific layers and gaps | Raster/archive/reference tests pass | Units, legends, layout and live sources |
| E09 | Physical phone | No executed device evidence | Touch, orientation, popups and layers |

## Evidence and exit gate

Record date/time, operator, browser/device, exact source commit, DEM hashes, route coordinates, request/status and screenshots. Establish resolution-aware tolerance before comparing points. Suite duration is not a route benchmark. Mark a check blocked/skipped when evidence is unavailable; never turn it into PASS because a related unit test passed. Final acceptance requires the team's documented decision about all remaining hardware/visual gates.
