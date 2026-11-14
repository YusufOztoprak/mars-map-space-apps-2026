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

The CTX DEM supports crater-scale relative route analysis. It cannot resolve foot-scale rocks or certify that a route is safe. Do not describe the HiRISE image tiles as the terrain input for slope calculations.

### Global MOLA scope decision

A global MOLA DEM is not required for the Jezero MVP and is not used by the current route calculation. The local route uses the 20 m CTX DEM. Whole-Mars coverage remains future scope; any MOLA layer added later must be labeled as coarse regional context with its resolution and coverage limits.

## Software and imagery credits

- **Leaflet:** BSD 2-Clause license. Retain its copyright and license notice in distributed documentation or other materials: [official Leaflet license](https://github.com/Leaflet/Leaflet/blob/main/LICENSE).
- **HiRISE imagery:** credit **NASA/JPL/University of Arizona**. HiRISE images are public domain, and the team requests this credit where possible: [HiRISE image usage policy](https://www.uahirise.org/media/usage.php).

## Lake Salda pitch

Lake Salda in Türkiye is a useful Earth analogue for Jezero because both have carbonate-bearing deposits and lake/delta processes. Researchers use the comparison to help interpret Jezero's ancient environment; the two sites are distinct. Sources: [NASA Science](https://science.nasa.gov/blogs/earth-matters/2021/02/17/what-a-lake-in-turkey-can-tell-us-about-mars/) and [NASA Planetary Analog Explorer](https://science.nasa.gov/solar-system/analog-explorer/).

## Attribution and limits

NASA-led data are generally public domain unless a product's metadata says otherwise. Keep the NASA/JPL credit recorded with each image, follow the product-specific citation above, and do not use NASA insignia or imply NASA endorsement. External image and dataset terms can differ. Global weather and radiation forecasts are not part of this data package.