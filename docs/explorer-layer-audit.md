# Mars Explorer scientific layer audit

Historical 2026-11-14 report. The current audit, updated matrix validation, unrestricted-distance routing checks and remaining acceptance gaps are in [the 2026-11-15 final report](final-audit-2026-11-15.md).

Reviewed 2026-11-14. Implementation is in `C:/Projects/mars-map-space-apps-2026-explorer`, on an independent local `veri-icerik` branch imported from the supplied ZIP. The ZIP's Git merge state and virtual environment were not imported. The existing project checkout and its branches were not changed or pushed.

## Problems and corrections

1. **Radiation appeared empty at Jezero:** the only record was a regional Gale marker from a third-party export, outside the initial view. Added a direct jump to each archived observation, an explicit coverage message and a PDS-sourced RAD record with exact units, UTC, integration time, detached label and source evidence. Custom-heightmap ground clamping could also hide the symbol; observation markers now use sampled numerical ground heights with a small symbol offset and local depth-test override. This does not create a radiation footprint.
2. **Blur outside Jezero:** the old optical stack mainly used the 232 m Viking mosaic. Added a capabilities-derived manifest of 81 optical CTX/HiRISE mosaics. Only visible footprints are instantiated, with coarser products under finer ones and actual native levels/tile dimensions. The global CTX ResourceURL points to an external ArcGIS service; the guessed Trek tile path returned 404. Using the advertised template restored the global CTX imagery. The service's 512-pixel level-11 tiles provide approximately 10.18 m/pixel at the equator, rather than promising the nominal 5 m source sampling everywhere.
3. **Color keys did not match numeric interpolation:** the old CSS spread colors uniformly while the backend thresholds were nonuniform; dust had the same issue. Numeric keys now use the exact thresholds and palette from the backend or prepared dust metadata. Height defaults to 100% opacity; other opacity settings disclose blending. New relief uses elevation hues plus numerical hillshade; brightness is not another height value. Geology has unit/color/name keys, explicitly marked as an application palette.
4. **Rendering and route grids could disagree:** a route uses one DEM, while auto rendering could silently switch to finer terrain partway through it. Quantitative tiles and point inspection now lock to the selected route's DEM. Missing cells outside that DEM remain transparent/null, without falling back to another model. Clear restores automatic sampling. The 3D geometry footer is explicitly separate from the analysis grid.
5. **Environmental interpretation:** TES color imagery has no verified numerical palette calibration here, THEMIS is relative infrared brightness, and daily historical dust is not present-day weather. Their UI text states those limits. Archived RAD/MEDA points are not extrapolated into global environmental maps or treated as route-time measurements.

## Layer status, provenance and scientific meaning

All angular coordinates are planetocentric latitude and east-positive longitude. Optical and numerical tiles use geographic 2:1 matrices on the Mars sphere, not Web Mercator. The local raster transforms come from the GeoTIFF product. The manifest records individual footprints, capabilities URLs, levels, served pixel sizes, mission/instrument, timestamps of review and credits. Source mosaic acquisition dates vary by contributing image.

| Layer | Status and coverage | Values, source and interpretation |
|---|---|---|
| Surface imagery | Working; global context and nonuniform high-resolution footprints | Viking 232 m fallback; MRO CTX global service ≈10.18 m served pixels; regional CTX/HiRISE. [NASA Mars Trek capabilities](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars). Source texture gaps and seams remain visible. |
| Elevation | Working; global coarse MOLA, local CTX and small HiRISE window | Numerical meters relative to Martian areoid. [MOLA MEGDR](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html): 16 px/degree ≈3.7 km, 1997–2001 collection described by label. [Jezero CTX DEM](https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic): 20 m. [HiRISE stereo DTM](https://hirise.lpl.arizona.edu/dtm/PSP_002387_1985): ≈1.02 m over the supplied small window. |
| Physical/topographic relief | Working on those same DEMs | Same elevation palette, NW light at 45° altitude; shaded brightness is illustrative illumination. No external hillshade image is used as numerical terrain. |
| Slope | Working, DEM-dependent | Degrees from DEM gradients. 15–20° warning; >20° excluded by prototype routing. Coarse MOLA slopes cannot resolve small hazards. |
| Roughness | Working, DEM-dependent | Meters: center-height difference from the mean of four neighbors. Resolution-dependent proxy, not boulder detection or measured footing stability. |
| Geology | Working; local Jezero map and global small-scale units | [USGS SIM 3464](https://pubs.usgs.gov/publication/sim3464), 1:75,000; [SIM 3292](https://pubs.usgs.gov/sim/3292/), 1:20,000,000. Application colors identify named units; no inferred ground-strength risk. |
| Radiation | Working local archived point; global/current coverage missing | [NASA PDS MSL RAD RDR](https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/): OBS000 E detector, Sol 1500, 10.92457 µGy/h, 2016-10-24 19:33:55 UTC, 961 s integration. Associated with same-sol NASA endpoint, not exact observation coordinates. Absorbed dose rate is not dose equivalent in sieverts. |
| Thermal inertia | Working as source-rendered context; numerical calibration missing | MGS/TES `TES_Thermal_Inertia`, WMTS levels 0–1. Physical inertia units are J m⁻² K⁻¹ s⁻½, but pixel colors are not assigned values without a verified key. No route factor. |
| Nighttime infrared | Working within approximately ±65° | Odyssey/THEMIS controlled nighttime mosaic, nominal 100 m. Relative infrared brightness, not Kelvin or air temperature. |
| Temperature | Working single archived MEDA point; global/current coverage missing | Perseverance ATS sensor 1, Sol 1, LTST 15:27:28. [PDS calibrated ATS CSV](https://atmos.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_calibrated_env/sol_0000_0089/sol_0001/WE__0001___________CAL_ATS_________________P01.CSV): independently checked source row 253.31 K → −19.84 °C. Approximate Jezero landing location. |
| Dust | Working historical observation-interpolated model | Montabone v2.5, MY34 Sol 400 (Ls 196.39°), 3° grid; dimensionless 9.3 µm column optical depth normalized to 610 Pa. [Dataset](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/). Shared metadata ties legend to prepared texture. |
| Atmosphere | Historical dust context only | No global current air temperature, wind, pressure or forecast grid is supplied. MEDA remains a point record; dust is not a complete atmosphere simulation. |
| Data coverage | Working numerical cell mask and point/route coverage summaries | Teal CTX and purple HiRISE valid cells; transparent does not imply no global MOLA. Point panel reports terrain, optical footprints, geology, historical dust and environmental gaps. Footprints do not guarantee valid image pixels. |
| Historical rover routes | Working archived geometries | NASA/JPL MMGIS Perseverance/Curiosity and PDS corrected Spirit/Opportunity tracks. Checked all four selectors. Missing Curiosity sol attributes are disclosed rather than reconstructed. Distance is the archived track length, not a current mission odometer. |

## Routing, validation and evidence

- Actual CTX route in the browser: shortest 1.644 km, maximum slope 16.1°; balanced 1.644 km / 11.7°; smoother 1.679 km / 10.3°. Alternatives and the orange steep-slope segment rendered. Radiation, route-time temperature and dust remained missing (0% coverage), visually distinct from slope warnings. Displaying an environmental layer does not make it a routing cost.
- Clicking the surface returned elevation −2473.72 m, slope 10.9° and roughness 0.94 m from the selected CTX analysis grid, alongside USGS unit `NHjf2`, historical dust and explicit environmental gaps.
- **27 backend tests passed** using the supplied real MOLA, CTX and HiRISE files: existing routes/validation plus RAD byte pointer, units/time/waypoint provenance, source-excerpt checksum, raw MOLA cell → point → raster palette consistency, model-specific no-data masks, relief transparency/hue behavior, advertised CTX template/tile size, and dust texture/palette consistency. [Recorded run](explorer-tests.txt).
- JavaScript syntax check passed. Browser checks covered optical switching, global numerical colors/relief, each scientific layer control/key, local RAD/MEDA records, unit legend, point inspection, real CTX routes and all four rover selectors. [Rover UI results](explorer-browser-traverses.json).
- **Eight representative remote tiles returned HTTP 200, decodable nonconstant imagery and CORS `*`**, including global CTX, Gale, Olympus, Jezero CTX/HiRISE, TES and both THEMIS mosaics. [Live service results](explorer-source-checks.json). All 81 capabilities were parsed; every pixel of every mosaic was not independently checked. Remote outages, irregular image gaps and registration seams remain possible, with a visible fallback message.
- This is not a claim that the older root Git-snapshot/integration suite or every browser/device combination passed; those were not used for this audit.

Screenshots: [RAD + Gale imagery](screenshots/rad-pds-verified.png), [global relief](screenshots/global-relief-verified.png), [CTX route + missing data](screenshots/ctx-route-verified.png).

## Reuse, repeatability and remaining limits

Detailed attribution and policy links are in [data_sources.md](../data_sources.md). NASA/JPL mission imagery retains mission/instrument/team credits; HiRISE requests NASA/JPL/University of Arizona attribution. USGS-authored data are generally US public domain with product-specific exceptions. Caltech/Murray Lab imagery is streamed from the NASA-advertised service; no separate redistribution license was independently established. The existing dust derivative retains CC BY-SA 3.0 obligations. Software licenses remain distinct.

Run `python scripts/verify_explorer_sources.py` to refresh official optical metadata and the RAD evidence without downloading global image mosaics. The supplied numerical data remain local and large DEMs stay ignored by Git. From this folder, the prepared local environment runs the reviewed app as:

```powershell
.\.venv\Scripts\python.exe -c "import sys;sys.path.insert(0,'backend');from app import app;app.run(host='127.0.0.1',port=5051,debug=False)"
```

Open `http://127.0.0.1:5051/`. For a fresh environment, install `backend/requirements.txt` and retain the supplied `data` products. Official data refresh needs network access. The old offline preprocessing scripts additionally need their existing GIS/NetCDF dependencies; those are not required for serving the app.

Global high-resolution DEM coverage, global radiation/current-weather fields, calibrated numerical TES retrieval, time-matched RAD positions and operational astronaut safety validation remain unavailable. Unknown values are never interpreted as zero risk. Coarse MOLA routing, a 20° prototype threshold and an adapted walking-cost model do not establish astronaut traversability.
