# Data Sources & Attribution

Last reviewed: 2026-11-14.

## Science points

`data/science_points.json` contains five Perseverance science and mission-context markers. Coordinates are GeoJSON `[longitude, latitude]` waypoint positions from the Perseverance mission map. They mark rover drive endpoints near the named targets, not exact drill or abrasion locations. Each feature records its waypoint sol, coordinate accuracy, one-sentence science summary, image gallery and preview URLs, caption, image credit, and supporting sources.

- Waypoint data: [Perseverance M20 waypoint GeoJSON](https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json). Credit: NASA/JPL-Caltech.
- Brac / South Séítah: [Mars rock samples](https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/) and [Brac Mastcam-Z panorama](https://science.nasa.gov/resource/mastcam-zs-view-of-the-area-around-brac-in-mars-jezero-crater/). The app preview uses a 1200 × 254 derivative of the natural-color panorama; the full NASA image is 26864 × 5694. Credit: NASA/JPL-Caltech/ASU/MSSS. The separate raw-image-gallery page is also retained in the feature; its default download is 128 × 128.
- Hogwallow Flats: [Mastcam-Z views](https://science.nasa.gov/resource/perseverances-mastcam-z-views-hogwallow-flats/) and [Jezero delta exploration](https://science.nasa.gov/resource/perseverance-explores-the-jezero-crater-delta/). Image credit: NASA/JPL-Caltech/ASU.
- Wildcat Ridge: [Mars rock samples](https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/) and [Hazeltop and Bearwallow samples](https://www.jpl.nasa.gov/videos/meet-the-mars-samples-hazeltop-and-bearwallow-samples-1213/). Image credit: NASA/JPL-Caltech.
- Yori Pass: [Perseverance investigates Martian bedrock](https://www.nasa.gov/missions/mars-2020-perseverance/perseverance-rover/nasas-perseverance-rover-investigates-intriguing-martian-bedrock/) and [Yori Pass context](https://science.nasa.gov/blog/a-picture-is-worth-a-thousand-words/). Image credit: NASA/JPL-Caltech/ASU.
- Three Forks Sample Depot: [NASA sample depot map](https://science.nasa.gov/resource/perseverances-three-forks-sample-depot-map/). This is a sample-recovery and mission waypoint. Image credit: NASA/JPL-Caltech.

Preserve each feature's `image_credit` and `image_caption` when showing an image. Context images are not necessarily photographs of the exact sampled rock.

## Map and terrain

- **NASA Mars Trek WMTS — Jezero HiRISE orthomosaic:** [Layer capabilities](https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0/WMTSCapabilities.xml). The layer is about 25 cm/pixel and is for visual context; it is not an elevation raster. Tile template: `https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0//default/default028mm/{z}/{y}/{x}.png`.
- **USGS Mars 2020 Science Investigation CTX DEM Mosaic:** [Product record and metadata](https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic); [direct GeoTIFF](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif). Resolution is 20 m/pixel; file size is about 87 MB. The DEM is tied vertically to MOLA. The product uses a Mars equirectangular projection, planetocentric latitude, and positive-east longitude. Credit Fred Calef / USGS Astrogeology Science Center; data originator: Planetary Data System. The product is public domain; cite the product authors.
- **NASA Mars Trek WMTS — MGS MOLA, Global Color Hillshade:** [Mars Trek layer catalog](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars), layer ID `Mars_MGS_MOLA_ClrShade_merge_global_463m` (~463 m/pixel, global coverage). Display attribution: **MOLA: NASA/JPL/GSFC · NASA Mars Trek**. NASA identifies the MOLA instrument as part of Mars Global Surveyor and uses the credit NASA/JPL/GSFC for its MOLA topographic imagery: [NASA/JPL MOLA reference](https://www.jpl.nasa.gov/images/pia01049-regional-topographic-views-of-mars-from-mola/).

The CTX DEM supports crater-scale relative route analysis. It cannot resolve foot-scale rocks or certify that a route is safe. Do not describe the HiRISE image tiles as the terrain input for slope calculations.

### Global MOLA layer and route scope

In the legacy 2D map, the optional 463 m/pixel MOLA color hillshade is visual context only. The 3D Explorer also reads separate numerical MOLA MEGDR rasters (16 pixels/degree, approximately 3.7 km) for regional terrain analysis outside the local CTX/HiRISE DEMs. These are different products: the color hillshade is never used as a numerical DEM. Regional routes on coarse MOLA cells cannot establish walkable terrain or astronaut safety. See [Explorer sources and method](docs/explorer-data.md).

### Explorer source verification

The [optical product manifest](data/explorer/imagery.json) enables 77 Mars Trek optical WMTS footprints and records four rejected inconsistent matrices. It stores advertised tile templates, native levels, tile dimensions, served equatorial pixel size, mission, instrument, credits and source capabilities URLs. The global Caltech CTX product is advertised by Mars Trek but serves tiles from `astro.arcgis.com`; constructing a Trek tile path for it returns 404. Its advertised maximum level is 11 with 512-pixel tiles (approximately 10.18 m/pixel at the equator), although the underlying mosaic is nominally 5 m/pixel. The sparse global HiRISE mosaic's repeated z11 matrix dimensions at z12–17 are corrected using its [publisher LOD metadata](https://astro.arcgis.com/arcgis/rest/services/OnMars/HiRISE/MapServer?f=pjson), which gives approximately 0.16 m served pixels at level 17. Served pixel size does not establish native acquisition detail or complete coverage. Regional mosaics activate when finer and covering the view; sparse global HiRISE is restricted to close zoom. Footprints may contain gaps and uncontrolled mosaics may show seams.

RAD now uses the official [NASA PDS PPI calibrated RDR archive](https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/), product `RAD_RDR_2016_298_19_33_1500_V00`, observation 000, E detector: **10.92457 µGy/h**, UTC **2016-10-24 19:33:55**, integration **961 seconds**. Source excerpt, full detached label, same-sol NASA rover waypoint and checksum are retained in `data/explorer/rad-sol1500/`. The label's byte pointer and unit define the numerical interpretation. The instrument file's zero geometry fields are placeholders; the marker uses the NASA Sol 1500 endpoint at 137.3550896° E, −4.70014911° N, explicitly labeled as a same-sol association, not the exact instrument position. This replaces the unlocated third-party export. No surrounding radiation field or route dose is inferred.

Reuse policy references: [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/), [USGS copyrights and credits](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits), and [HiRISE image policy](https://www.uahirise.org/media/usage.php). Retain product/team credits; do not imply NASA endorsement. Caltech CTX acknowledgment includes the Murray Lab, NASA/JPL and MSSS; a separate redistribution license for that mosaic was not independently established, so this app streams the advertised service and does not redistribute its imagery. The existing Montabone dust derivative remains CC BY-SA 3.0. Code licenses are separate from scientific data terms.

## Software and imagery credits

- **Leaflet:** BSD 2-Clause license. Retain its copyright and license notice in distributed documentation or other materials: [official Leaflet license](https://github.com/Leaflet/Leaflet/blob/main/LICENSE).
- **HiRISE imagery:** credit **NASA/JPL/University of Arizona**. HiRISE images are public domain, and the team requests this credit where possible: [HiRISE image usage policy](https://www.uahirise.org/media/usage.php).

## Lake Salda pitch

Lake Salda in Türkiye is a useful Earth analogue for Jezero because both have carbonate-bearing deposits and lake/delta processes. Researchers use the comparison to help interpret Jezero's ancient environment; the two sites are distinct. Sources: [NASA Science](https://science.nasa.gov/blogs/earth-matters/2021/02/17/what-a-lake-in-turkey-can-tell-us-about-mars/) and [NASA Planetary Analog Explorer](https://science.nasa.gov/solar-system/analog-explorer/).

## Attribution and limits

NASA-led data are generally public domain unless a product's metadata says otherwise. Keep the NASA/JPL credit recorded with each image, follow the product-specific citation above, and do not use NASA insignia or imply NASA endorsement. External image and dataset terms can differ. Global weather and radiation forecasts are not part of this data package.
