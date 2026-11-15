# Integration test report

Updated 15 November 2026. Product source baseline: main `008cf734fab40d5cad606170b37f6435d60775be`, with integration-only changes on `entegrasyon-test`. No backend/frontend product files were modified.

## Latest execution

| Suite | PASS | FAIL | SKIP | Evidence |
| --- | ---: | ---: | ---: | --- |
| Full root pytest, real CTX + MOLA available | 103 | 0 | 0 | [Output](current-full-tests.txt), 6.13 s |
| Integration subset (included in root total) | 58 | 0 | 0 | [Output](current-integration-tests.txt) |
| Current 2D frontend flow | 12 | 0 | 0 | [Output](frontend-test-output.txt) |
| Current Explorer imagery policy | 6 | 0 | 0 | [Output](current-explorer-policy.txt) |

These totals overlap; do not add the integration subset to the full pytest total.

## Test maintenance completed

Backend snapshot and frontend-flow tests now read checked-out source files by default, rather than silently testing an old Git commit. Source-directory overrides remain available for explicit external reviews. The backend fixture isolates copied Python modules in a temporary folder and restores module imports afterward. Only its DEM loader boundary is replaced for synthetic/error cases; actual product code is unchanged.

Four implemented checks replaced obsolete pending placeholders: missing DEM -> JSON 503, corrupt DEM -> JSON 503, a real route's cells are finite/traversable and <=20 degrees, and geographic-to-pixel conversion matches independent Rasterio projection. Browser/device requirements were moved to the manual checklist, not declared passed or hidden as generic skips.

## Data and environment

CTX SHA-256: `BA7F706EA1B5D63A562F28A7DCF7A7F3C79BCE7F048E6974B57E8A33C30D1BA2`.
MOLA SHA-256: `D18D9B9AB8C5516D02E157DD2CDE0F1D0D160C21940E953BA22391269A545E7B`.
Both files were verified previously and copied from the clean rehearsal clone into ignored data paths. They must not be committed.

The complete run used the clean rehearsal Python environment (Python 3.12.14, current backend requirements including Pillow). Initial attempts in the older environment encountered temporary-folder permissions and missing Pillow; the final outputs above supersede those setup failures.

From the repository root, install backend and test requirements in an isolated environment, obtain both README terrain downloads, then run:

```powershell
python -m pytest -v --tb=short
node --test tests/frontend-flow.cjs
node --test tests/explorer-policy.cjs
```

`MARS_TEST_DEM` optionally selects the real DEM used by integration fixtures; by default it is data/jezero_dem.tif. Without it, those real integration cases skip explicitly; some upstream audit tests still require downloaded products. A full no-data clone is not equivalent to this data-equipped acceptance run.

## Scope and limits

Current backend tests cover CTX/HiRISE/global routes, corner cutting, scientific archive evidence, raster contracts and independent numerical references. The 2D Node suite executes current application code with HTTP/Leaflet/DOM doubles; policy tests cover selection logic, not WebGL. Zero automated skips does not mean physical-phone/Chrome acceptance is complete. See [frontend checklist](frontend-checklist.md) and [readiness](readiness-report.md).
