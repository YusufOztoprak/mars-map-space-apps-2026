# Mars Explorer 2D and 3D validation

## A. 2D map

**Working.** The old header link opened the classic Leaflet Jezero page. The new control switches the existing Cesium viewer between the globe and a whole-Mars equirectangular map. Both modes share location search, point inspection, imagery, scientific layers, route state and rover tracks. Regional camera position is restored when switching. At world scale the flat view fits the full planet. Routes crossing 180° are split at the edges of the flat map. The flat map uses a planar surface and the same data overlays, avoiding 3D terrain mesh requests during flat navigation.

## B. Elevation data coverage

**Working.** The previous layer only sampled CTX and HiRISE, so areas covered by MOLA appeared transparent. Each new coverage pixel samples the installed grids and shows the finest valid height. The coverage key separates HiRISE (1.02 m), CTX (20 m), MOLA (3,705 m at the equator), and cells with no valid elevation. The PDS MOLA companion grid distinguishes cells with direct observations from cells whose heights were interpolated by the producer. Elevation and relief still use their own numeric height palette in meters relative to the areoid.

The local CTX mosaic contains 22,564,575 valid cells and 13,977 NoData cells. A real CTX NoData cell at 18.435353° N, 78.582385° E returned no height on the CTX model and valid MOLA coverage. The installed HiRISE crop has 1,040,400 valid cells. The MOLA grid supplies 16,588,800 elevation values, including 903,558 cells with zero observations in the count product. Unit checks confirmed source colors at matching raster and point coordinates, longitude wrapping, coverage independent of the route model, and explicit missing data when no grid provides a value.

The geographic tile grid uses planetocentric latitude and east-positive longitude. MOLA columns wrap from 0°–360° into the map's −180°–180° domain. CTX and HiRISE use the Mars sphere and their own GeoTIFF transforms. Chromium screenshots confirmed both CTX and HiRISE colors inside the rendered map in each view, outside the legend. At world zoom, small regional patches can be smaller than a display pixel. The HiRISE coverage shown is the installed Jezero crop.

## C. Map layers

| Feature | Status | Scope |
| --- | --- | --- |
| Surface imagery | Partially working | Viking fallback and verified CTX/HiRISE tiles. The external global CTX service returned HTTP 500 for one requested coarse tile. The app keeps coarser imagery and displays a tile warning. |
| Elevation and topographic relief | Working | DEM height palette and DEM-derived shaded relief in meters. |
| Elevation data coverage | Working | Valid cells and source resolution in both map modes. |
| Slope and roughness | Working | DEM gradients and neighborhood elevation differences. |
| Geology | Working | USGS regional and global polygons, unit legend and point query. |
| Radiation | Partially working | One calibrated historical RAD point near Gale. Current and global radiation coverage is unavailable. |
| Temperature | Partially working | One calibrated historical MEDA measurement near the Jezero landing site. |
| Thermal inertia | Partially working | Source-rendered TES imagery. Numerical values are unavailable from the displayed colors. |
| Nighttime infrared | Working | Archived THEMIS brightness imagery in its approximate ±65° latitude range. |
| Dust and atmosphere | Partially working | MY34 Sol 400 optical depth model. Current weather and atmospheric forecasts are unavailable. |
| Rover tracks | Working | Perseverance, Curiosity, Spirit and Opportunity archives. All four tracks painted in both views after batching same-style segments, including the 21,104-segment Opportunity archive. |

## D. Route system

| Real-data case | Grid | Result |
| --- | --- | --- |
| Jezero, 18.44° N 77.42° E to 18.46° N 77.40° E | CTX | **Working.** Three candidates. Shortest 1.656 km at 16.1° maximum modeled slope with one warning. Smoother 1.691 km at 10.3°. |
| Jezero stereo crop | HiRISE | **Working.** Three candidates around 34–35 m. |
| Gale Crater | MOLA | **Working.** Three candidates, 29.159–38.741 km. First candidate had two steep segment warnings and a 15.1° maximum modeled slope. |
| Amazonis Planitia | MOLA | **Working.** One distinct candidate, 60.638 km. |
| Antimeridian | MOLA | **Working.** 40.527 km from 179.8° E to 179.6° W. |
| CTX start on a 26.42° cell | CTX | **Working.** API rejected the route with HTTP 422 under the prototype 20° limit. |

A Jezero route calculated in the flat view retained the same cards after switching to the globe. Chromium read the orange steep segment and dashed purple gap colors directly from the route canvas in each view. The antimeridian route did not paint a line through the center of the world view.

Returned distances matched Mars great-circle sums along the returned geometry within the API rounding. Endpoints matched the requested coordinates. Route-time radiation, temperature and dust coverage were reported as missing when no matching observations were available.

## E. Scientific sources

- Viking, CTX and HiRISE optical imagery, TES thermal inertia and THEMIS nighttime infrared come from the linked NASA services and their source publishers. Eight representative tiles returned HTTP 200 and decoded as images. [NASA Mars Trek WMTS](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars)
- Global topography and observation counts use the Mars Global Surveyor laser altimeter archive. Jezero heights use the USGS stereo CTX mosaic and the HiRISE depositional fan stereo product. [NASA PDS MOLA MEGDR](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html) · [USGS Jezero CTX](https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic) · [HiRISE DTM](https://hirise.lpl.arizona.edu/dtm/PSP_002387_1985)
- Jezero geology is published at 1:75,000 and global geology at 1:20,000,000. [USGS SIM 3464](https://pubs.usgs.gov/publication/sim3464) · [USGS SIM 3292](https://pubs.usgs.gov/publication/sim3292)
- The radiation archive supplies a Curiosity RAD E absorbed dose rate of 10.92457 µGy/h for the recorded observation. The map marker follows a same-sol rover position. MEDA supplies the archived local air temperature of −19.84 °C. The dust grid is an interpolation of historical orbital observations at 3° × 3°. [NASA PDS RAD](https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/) · [NASA PDS MEDA](https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/PERSEVERANCE/meda.html) · [Montabone dust climatology](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/)
- Rover traces are archived geometries and the place-name index uses the USGS/IAU gazetteer. [NASA Perseverance](https://science.nasa.gov/mission/mars-2020-perseverance/location-map/) · [NASA Curiosity](https://science.nasa.gov/mission/msl-curiosity/location-map/) · [PDS Spirit and Opportunity](https://an.rsl.wustl.edu/mera/AN/pages/mer/mer_traverse.htm) · [USGS/IAU Gazetteer](https://planetarynames.wr.usgs.gov/Page/MARS/target)

## F. System status

- **Working.** 101 Python tests passed. Six pre-existing integration scenarios were skipped by their placeholder test. Twelve JavaScript flow tests passed. The Explorer JavaScript passed syntax checking.
- **Working in desktop Chromium.** Checked world view, drag and zoom, placement of selected coordinates, camera restoration, data queries, overlay toggles and opacity, rapid toggles, archived observation panels and all four rover tracks. The focused mode and routing run had no application JavaScript exceptions or local HTTP errors.
- **Not tested.** Physical mobile devices, Safari and Firefox were outside this run. Representative imagery requests cover a sample of each selected service.
- **Remaining limits.** Detailed terrain is confined to the installed regional grids. MOLA supports coarse regional planning. The considered slope thresholds and estimated walking times describe prototype calculations. Further work could add regional DEM coverage, expand GPU and browser regression coverage and add time-matched environmental observations where available.
