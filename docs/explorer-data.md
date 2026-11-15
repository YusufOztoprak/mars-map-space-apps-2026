# Mars Explorer data and routing method

| Layer | Product and use |
| --- | --- |
| Global imagery | NASA/JPL Mars Trek Viking MDIM 2.1. Two low-zoom tiles are bundled. Higher-resolution tiles stream from Mars Trek. [Mars Trek](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars) |
| Jezero imagery | NASA Mars Trek CTX 6 m and HiRISE 25 cm orthomosaics. Zoom and coverage determine which imagery is shown. [Mars Trek](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars) |
| Fine elevation | NASA/USGS HiRISE stereo DTM DTEEC_002387_1985_003798_1985_A01. The approximately 1 × 1 km window centered at 77.41° E and 18.45° N retains the original 1.02 m samples. [HiRISE product](https://hirise.lpl.arizona.edu/dtm/PSP_002387_1985) · [USGS collection and CC0](https://doi.org/10.5066/P9VQTS7V) |
| Elevation | Original MGS/MOLA MEGDR topography grids at 16 and 4 pixels per degree, approximately 3.7 km and 14.8 km at the equator. The USGS Jezero CTX Science Investigation DEM provides 20 m cells. Elevations are in meters relative to the Martian areoid. [MOLA](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html) · [CTX](https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic) |
| Geology | Sun and Stack's Jezero map (USGS SIM 3464, 1:75,000) and Tanaka et al.'s global map (USGS SIM 3292, 1:20,000,000). Global units came from the USGS ArcGIS service. Local units were transformed from the original geodatabase to geographic Mars coordinates. The geometries were simplified for web display. [SIM 3464](https://pubs.usgs.gov/publication/sim3464) · [SIM 3292](https://pubs.usgs.gov/publication/sim3292) · [Global feature service](https://services.arcgis.com/nzS0F0zdNLvs7nc8/ArcGIS/rest/services/Mars_Geology_feature_layer/FeatureServer) |
| Thermal context | TES thermal inertia and Mars Odyssey THEMIS nighttime infrared mosaics provide historical surface context. [Mars Trek](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars) |
| Air temperature | Perseverance MEDA ATS sensor 1, Sol 1, 15:27:28 local true solar time. The sample was converted from Kelvin to Celsius. The marker is at the approximate landing site. [NASA PDS measurement archive](https://atmos.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_calibrated_env/sol_0000_0089/sol_0001/) |
| Radiation | Curiosity RAD E detector, Sol 1500. The first published archive row provides an absorbed dose rate in µGy/day. The Gale marker indicates the region. The sample is from Heber and Löwe's CC BY 4.0 archive. [NASA RAD](https://data.nasa.gov/dataset/mars-science-laboratory-msl-radiation-assessment-detector-rad-level-2-observation-dosimetr) · [Data release](https://doi.org/10.5281/zenodo.20536564) |
| Dust | Montabone et al., v2.5, Mars Year 34, Sol 400. A daily 3° × 3° atmospheric column optical depth grid interpolated from orbital observations at 9.3 µm and normalized to 610 Pa. The JSON extract and colorized PNG retain the source's [CC BY-SA 3.0 license](https://creativecommons.org/licenses/by-sa/3.0/). [Dataset](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/) · [Paper](https://doi.org/10.1029/2019JE006111) |
| Place names | USGS/IAU Gazetteer center coordinates. East-positive longitudes were converted from 0–360° to −180–180°. [Gazetteer](https://planetarynames.wr.usgs.gov/Page/MARS/target) |
| Rover traverses | NASA/JPL MMGIS lines for Perseverance and Curiosity. NASA PDS Geosciences Node corrected tracks for Spirit and Opportunity include some archive-interpolated intermediate positions. The app preserves line boundaries and available sol fields and computes distances from the archived geometry. [Perseverance](https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json) · [Curiosity](https://mars.nasa.gov/mmgis-maps/MSL/Layers/json/MSL_traverse.json) · [Spirit and Opportunity](https://an.rsl.wustl.edu/mera/AN/pages/mer/mer_traverse.htm) |

The CesiumJS 1.132.0 distribution and license are in `frontend/vendor/cesium`.
The Leaflet license and Perseverance science site credits are listed in [Data sources and attribution](../data_sources.md).

## Routing and coverage

- The 3D globe uses a spherical Mars 2000 reference radius of 3,396,190 m with planetocentric latitude and east-positive longitude. Elevation detail switches from MOLA to CTX near Jezero, then to HiRISE within the bundled stereo window at higher zoom. Imagery, terrain rendering, and analysis can use different resolutions.
- Each route uses one elevation grid. The straight-line distance limit is 30 km for Jezero and 1,200 km for MOLA. MOLA routing accepts endpoints within ±87° latitude. The search uses a bounded window and expansion budget. The route summary reports the offset between the requested coordinates and the selected cell centers.
- The search excludes cells above the prototype 20° slope limit and cells without valid elevation or slope. Diagonal moves require both adjacent cells to be passable. Segments at or above 15° receive a slope warning.
- Surface roughness is the absolute difference between a cell's elevation and the mean elevation of its four neighbors. Route profiles apply different weights to slope and roughness. Identical candidate paths share a single route card.
- Coverage applies to sampled route cells. Geology coverage reflects mapped unit boundaries. Archived temperature and radiation measurements are point samples. The dust layer describes a historical sol. The route planner reports gaps in environmental data that lack matching locations and times.
- The 20 m CTX grid cannot resolve boulders or small fissures. MOLA supports regional planning. The approximately 1 m HiRISE grid is selected when both endpoints have valid elevation inside the bundled stereo window.


## Rebuild the display layers

The app ships the display layers in `data/explorer/`. The preparation scripts read local downloads from `data/raw/` and write regenerated assets to `data/processed/explorer/`. Review the output before copying selected files into `data/explorer/`.

Install the optional processing dependencies with `python -m pip install geopandas pyproj scipy` after installing the app dependencies.

- For `python scripts/prepare_mars_explorer.py`, use the sources in the table above. Save the Viking tiles as `viking0.png` and `viking1.png`, the gazetteer shapefile archive as `names.zip`, the two MMGIS traverses as `perseverance.json` and `curiosity.json`, and the MER traverse shapefile archives as `spirit.zip` and `opportunity.zip`. Extract the Jezero geodatabase as `Nili.gdb`. For global geology, save the geographic features as `global-geology.json` or the full ArcGIS query response for the Martian-coordinate layer as `global-esri.json`. Optional point observations use `meda.csv` (the calibrated Sol 1 ATS export) and `rad-dose.txt` (the tab-separated RAD E dose archive).
- For `python scripts/prepare_mars_dust.py`, save the [MY34 daily dust scenario NetCDF](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/dataset_v2/dustscenario_MY34_v2-5.nc) as `dust.nc`. The script extracts Sol 400 and writes the PNG and JSON used by the app.
- Download CTX and MOLA to their runtime locations using the [README](../README.md#download-terrain-data). To regenerate the 2D slope overlay from the downloaded CTX mosaic, run `python backend/make_slope_overlay.py` from the repository root.
