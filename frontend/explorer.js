const $ = id => document.getElementById(id);
const C = window.Cesium;
const api = location.port === "8000" ? "http://localhost:5000" : "";
const data = "../data/explorer/";
const trek = "https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars";
const mola = "https://pds-geosciences.wustl.edu/missions/mgs/megdr.html";
const ctx = "https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic";
const jgeo = "https://pubs.usgs.gov/publication/sim3464";
const ggeo = "https://pubs.usgs.gov/publication/sim3292";
const meda = "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/PERSEVERANCE/meda.html";
const rad = "https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/";
const dustSource = "https://www-mars.lmd.jussieu.fr/mars/dust_climatology/";
const profileNames = {shortest: "Shortest", balanced: "Balanced", terrain: "Smoother terrain"};
const factorNames = {height:"Elevation", slope:"Slope", roughness:"Roughness", geology:"Geology",
  thermal:"Thermal context", temperature:"Air temperature", dust:"Atmosphere / dust", radiation:"Radiation"};
const roverSources = {
  perseverance:["Perseverance", "https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json"],
  curiosity:["Curiosity", "https://science.nasa.gov/mission/msl-curiosity/location-map/"],
  opportunity:["Opportunity", "https://an.rsl.wustl.edu/mera/AN/pages/mer/mer_traverse.htm"],
  spirit:["Spirit", "https://an.rsl.wustl.edu/mera/AN/pages/mer/mer_traverse.htm"],
};
const routeColors = ["#71e1d1", "#ffa772", "#94aaff"];

function el(tag, value, className) {
  const element = document.createElement(tag);
  if (value !== undefined) element.textContent = value;
  if (className) element.className = className;
  return element;
}

function link(label, url) {
  const a = el("a", label);
  if (/^https:\/\//i.test(url || "")) {
    a.href = url; a.target = "_blank"; a.rel = "noopener";
  }
  return a;
}

async function get(url, options) {
  const response = await fetch(url, options);
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || "HTTP " + response.status);
  return value;
}

function field(parent, title, value) {
  const row = el("div", undefined, "field");
  row.append(el("span", title), el("strong", value ?? "No data available"));
  parent.append(row);
}

function feedback(message) {
  $("map-feedback").textContent = message;
  $("map-feedback").hidden = !message;
}

const longitude = n => ((n + 180) % 360 + 360) % 360 - 180;
const fmt = (v, digits=1) => Number(v).toLocaleString("en-US", {maximumFractionDigits:digits});
const pointText = (lat, lon) => `${Math.abs(lat).toFixed(5)}° ${lat < 0 ? "S" : "N"}, ${Math.abs(lon).toFixed(5)}° ${lon < 0 ? "W" : "E"}`;
function parseCoords(value) {
  const m = value.trim().match(/^([+-]?\d+(?:\.\d+)?)\s*[, ]\s*([+-]?\d+(?:\.\d+)?)$/);
  if (!m || Math.abs(+m[1]) > 90 || Math.abs(+m[2]) > 360) return null;
  return {lat:+m[1], lon:longitude(+m[2])};
}

function opticalSelection(products,height,box) {
  const t=Math.min(1,Math.max(0,(1.6e6-height)/1e6));
  const detail=t*t*(3-2*t);
  const backdrop=products.filter(p=>p.bounds[2]-p.bounds[0]>350 && p.instrument==="CTX");
  const baseResolution=Math.min(...backdrop.map(p=>p.resolution_m));
  const regional=products.filter(p=>p.bounds[2]-p.bounds[0]<350 && p.resolution_m<baseResolution
    && box && box[0]<=box[2] && p.bounds[0]<=box[0] && p.bounds[1]<=box[1]
    && p.bounds[2]>=box[2] && p.bounds[3]>=box[3] && height<Math.max(1500,p.resolution_m*8000))
    .reduce((best,p)=>!best || p.resolution_m<best.resolution_m?p:best,null);
  return {detail,active:detail?products.filter(p=>backdrop.includes(p) || p===regional ||
    (p.id==="HiRISE_Global" && height<1500)):[]};
}

async function run() {
  if (!C) throw new Error("The 3D map library could not be loaded.");
  const ellipsoid = new C.Ellipsoid(3396190, 3396190, 3396190);
  C.Ellipsoid.default = ellipsoid;
  const tilingScheme = new C.GeographicTilingScheme({ellipsoid});
  const viewer = new C.Viewer("globe", {globe:new C.Globe(ellipsoid), baseLayer:false, baseLayerPicker:false,
    animation:false, timeline:false, geocoder:false, sceneModePicker:false, homeButton:false,
    infoBox:false, selectionIndicator:false, navigationHelpButton:false, fullscreenButton:false,
    requestRenderMode:true, skyAtmosphere:false, skyBox:false, mapProjection:new C.GeographicProjection(ellipsoid)});
  const scene = viewer.scene;
  scene.backgroundColor = C.Color.fromCssColorString("#0b0e15");
  if (scene.sun) scene.sun.show = false;
  if (scene.moon) scene.moon.show = false;
  scene.globe.enableLighting = false;
  scene.globe.baseColor = C.Color.fromCssColorString("#9a5c46");
  scene.globe.showGroundAtmosphere = false;
  scene.screenSpaceCameraController.minimumZoomDistance = 260;
  scene.screenSpaceCameraController.maximumZoomDistance = 45e6;
  viewer.screenSpaceEventHandler.removeInputAction(C.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
  const toRect = box => C.Rectangle.fromDegrees(...box);
  const cart = (lon, lat, h=0) => C.Cartesian3.fromDegrees(lon, lat, h, ellipsoid);
  const jezero = {lon:77.42,lat:18.45};
  const broad = {lon:66,lat:17};
  function fly(point, height=44000, duration=.8) {
    viewer.camera.flyTo({destination:cart(point.lon, point.lat, height), duration,
      orientation:{heading:0,pitch:-Math.PI/2,roll:0}});
  }
  fly(broad, 8e6, 0);
  $("planet").onclick = () => fly(broad, 8e6);
  $("jezero").onclick = () => fly(jezero);
  $("zoom-in").onclick = () => viewer.camera.zoomIn(Math.max(400, viewer.camera.positionCartographic.height*.30));
  $("zoom-out").onclick = () => viewer.camera.zoomOut(viewer.camera.positionCartographic.height*.52);

  function pick(position) {
    const ray = viewer.camera.getPickRay(position);
    const value = ray && (scene.globe.pick(ray, scene) || viewer.camera.pickEllipsoid(position, ellipsoid));
    if (!value) return null;
    const p = ellipsoid.cartesianToCartographic(value);
    return {lon:longitude(C.Math.toDegrees(p.longitude)),lat:C.Math.toDegrees(p.latitude)};
  }

  const selected = new C.CustomDataSource("Selected points");
  const planned = new C.CustomDataSource("Candidate routes");
  const mission = new C.CustomDataSource("Rover tracks");
  for (const source of [selected, planned, mission]) viewer.dataSources.add(source);
  function marker(source, w, color, title, info) {
    const reference=Number.isFinite(w.height)?C.HeightReference.NONE:C.HeightReference.CLAMP_TO_GROUND;
    const entity = source.entities.add({position:cart(w.lon,w.lat,w.height || 0), point:{
      pixelSize:10,color:C.Color.fromCssColorString(color),outlineColor:C.Color.fromCssColorString("#141722"),
      outlineWidth:2,heightReference:reference,disableDepthTestDistance:100000},
      label:title ? {text:title,font:"600 13px sans-serif",showBackground:true,backgroundColor:C.Color.BLACK.withAlpha(.74),
        pixelOffset:new C.Cartesian2(0,-16),heightReference:reference,disableDepthTestDistance:100000,
        distanceDisplayCondition:new C.DistanceDisplayCondition(0,250000)} : undefined});
    entity.readInfo = info;
    return entity;
  }
  const routeCanvas=$("route-canvas");
  const pencil=routeCanvas.getContext("2d");
  const routeStrokes=[];
  const roverStrokes=[];
  const roverHitPoints=[];
  const horizon=new C.EllipsoidalOccluder(ellipsoid);
  const screenPoint=new C.Cartesian2();
  function drawRoutes() {
    const {clientWidth:w,clientHeight:h}=scene.canvas;
    const ratio=window.devicePixelRatio||1;
    if (routeCanvas.width!==Math.round(w*ratio) || routeCanvas.height!==Math.round(h*ratio)) {
      routeCanvas.width=Math.round(w*ratio);
      routeCanvas.height=Math.round(h*ratio);
    }
    pencil.setTransform(ratio,0,0,ratio,0,0);
    pencil.clearRect(0,0,w,h);
    pencil.lineJoin="round";
    pencil.lineCap="round";
    horizon.cameraPosition=viewer.camera.positionWC;
    roverHitPoints.length=0;
    for (const stroke of [...roverStrokes,...routeStrokes]) {
      pencil.beginPath();
      let previous=false;
      let lastX=0,lastY=0;
      for (const point of stroke.points) {
        if (!horizon.isPointVisible(point.surface)) {previous=false;continue;}
        const px=C.SceneTransforms.worldToWindowCoordinates(scene,point.terrain,screenPoint);
        if (!px) {previous=false;continue;}
        if (previous && Math.hypot(px.x-lastX,px.y-lastY)<1) continue;
        if (stroke.readInfo && px.x>=0 && px.x<=w && px.y>=0 && px.y<=h)
          roverHitPoints.push({x:px.x,y:px.y,readInfo:stroke.readInfo});
        if (previous) pencil.lineTo(px.x,px.y);
        else pencil.moveTo(px.x,px.y);
        lastX=px.x;lastY=px.y;
        previous=true;
      }
      pencil.setLineDash(stroke.dash?[5,5]:[]);
      pencil.globalAlpha=stroke.alpha;
      pencil.lineWidth=stroke.width+2;
      pencil.strokeStyle="#10131d";
      if (!stroke.dash) pencil.stroke();
      pencil.lineWidth=stroke.width;
      pencil.strokeStyle=stroke.color;
      pencil.stroke();
    }
    pencil.globalAlpha=1;
  }
  scene.postRender.addEventListener(drawRoutes);
  function routeStroke(geometry, heights, color, width, dash=false, alpha=1) {
    routeStrokes.push({color,width,dash,alpha,points:geometry.map(([lon,lat],i)=>({
      surface:cart(lon,lat,1), terrain:cart(lon,lat,heights[i])
    }))});
  }
  let meta = {};
  let analysisModel="auto";
  let analysisSource="Finest available elevation at each point";
  let pointLock = 0;
  let pickMode = "inspect";
  let controls = {};
  let routeVersion = 0;

  function observationInfo(o) {
    pointLock++;
    const target = $("point-info");
    target.replaceChildren(el("h3", o.instrument));
    field(target,"Measurement", `${fmt(o.value,2)} ${o.unit}`);
    field(target,"Record", `Sol ${o.sol} · ${o.time}${o.id==="meda"?" LTST":""}`);
    field(target,"Location", o.location);
    if (o.duration_s) field(target,"Integration",`${o.duration_s} seconds`);
    if (o.coordinate_accuracy) target.append(el("p",o.coordinate_accuracy));
    if (o.dataset) field(target,"Dataset",o.dataset);
    target.append(el("p","Archived measurement for a specific place and time."),link("Measurement source",o.source));
    if (o.label_url) target.append(el("br"),link("PDS units and record label",o.label_url));
    if (o.location_source) target.append(el("br"),link("Same-sol rover position source",o.location_source));
  }

  async function inspect(point) {
    const lock = ++pointLock;
    const target = $("point-info");
    const label = pointText(point.lat, point.lon);
    $("coordinates").textContent = $("footer-coordinates").textContent = label;
    target.replaceChildren(el("p", label),el("p","Loading location data…"));
    try {
      const {terrain, geology, historical_dust, coverage} = await get(api + `/api/explorer/point?lat=${point.lat}&lon=${point.lon}&model=${analysisModel}`);
      if (lock !== pointLock) return;
      target.replaceChildren(el("p",label));
      for (const [key, unit] of [["height","m"],["slope","°"],["roughness","m"]]) {
        const value = terrain[key];
        field(target, factorNames[key], value ? `${fmt(value.value,2)} ${unit}` : null);
        if (value) target.append(link(`${value.source.name} · ${fmt(value.source.resolution_m,0)} m`,value.source.url));
      }
      field(target,"Geologic unit",geology ? `${geology.unit} · ${geology.name}` : null);
      if (geology) target.append(link(`Geology · ${geology.scale}`,geology.url));
      for (const key of ["radiation","temperature"]) field(target,factorNames[key],"No matching measurement at this point");
      field(target,"Historical dust model",historical_dust?
        `τ ${fmt(historical_dust.value,3)} · MY ${historical_dust.year}, Sol ${historical_dust.sol}`:null);
      if (historical_dust) target.append(link("MRO/MCS · Montabone et al.",historical_dust.url));
      target.append(el("p",meta.elevation_reference || "Elevation relative to the Martian areoid."));
      const available=(verifiedImagery.layers || []).filter(p=>contains(p.bounds,point));
      field(target,"Optical imagery footprints",available.length ?
        `${available.length} products; finest served pixel ≈ ${fmt(Math.min(...available.map(p=>p.resolution_m)),2)} m at equator` : "Viking context; no verified CTX/HiRISE footprint");
      target.append(el("p","Footprints do not guarantee valid pixels. Imagery gaps retain the coarser base map."));
      for (const [key,value] of Object.entries(coverage || {}))
        field(target,`${factorNames[key] || key} coverage`,value.status.replaceAll("_"," "));
      target.append(el("p","Missing environmental data are unknown, not zero risk. Archived point records do not establish route-time coverage."));
    } catch (error) {
      if (lock === pointLock) target.replaceChildren(el("p",label),el("p", "Could not load location data.", "status-error"));
    }
  }

  function setMode(mode) {
    pickMode = mode;
    $("pick-start").setAttribute("aria-pressed", String(mode === "start"));
    $("pick-end").setAttribute("aria-pressed", String(mode === "end"));
    feedback(mode === "inspect" ? "" : mode === "start" ? "Pick the starting point on the map" : "Pick the destination on the map");
  }
  $("pick-start").onclick = () => setMode(pickMode === "start" ? "inspect" : "start");
  $("pick-end").onclick = () => setMode(pickMode === "end" ? "inspect" : "end");
  const endpoints = {};
  function setEndpoint(id, point) {
    $(id).value = `${point.lat.toFixed(6)}, ${point.lon.toFixed(6)}`;
    if (endpoints[id]) selected.entities.remove(endpoints[id]);
    endpoints[id] = marker(selected,point,id === "start" ? "#71e1d1" : "#ffa772",id === "start" ? "Start" : "Destination");
  }
  const handler = new C.ScreenSpaceEventHandler(scene.canvas);
  handler.setInputAction(event => {
    if (pickMode === "inspect") {
      const hit = scene.pick(event.position);
      if (hit?.id?.readInfo) { hit.id.readInfo(); return; }
      const roverHit=roverHitPoints.find(p=>Math.hypot(p.x-event.position.x,p.y-event.position.y)<6);
      if (roverHit) { roverHit.readInfo();return; }
    }
    const point = pick(event.position);
    if (!point) return;
    if (pickMode !== "inspect") setEndpoint(pickMode, point);
    setMode("inspect");
    inspect(point);
  }, C.ScreenSpaceEventType.LEFT_CLICK);

  const wmts = (id, ext, max, bounds, attribution) => new C.UrlTemplateImageryProvider({
    url:`https://trek.nasa.gov/tiles/Mars/EQ/${id}/1.0.0/default/default028mm/{z}/{y}/{x}.${ext}`,
    tilingScheme, maximumLevel:max, rectangle:bounds && toRect(bounds), credit:attribution || "NASA/JPL Mars Trek",
    enablePickFeatures:false,
  });
  const localRaster = name => new C.UrlTemplateImageryProvider({
    url:api + `/api/explorer/raster/${name}/{z}/{x}/{y}.png?model=${analysisModel}`, tilingScheme, maximumLevel:17, enablePickFeatures:false,
  });
  const addImages = (providers, baseIndex) => providers.map((provider, i) => {
    provider.errorEvent.addEventListener(event => {
      event.retry = false;
      $("imagery-status").textContent="Some remote tiles could not load. Coarser imagery remains underneath; source coverage may contain gaps.";
    });
    return viewer.imageryLayers.addImageryProvider(provider, baseIndex === undefined ? undefined : baseIndex+i);
  });
  const cache = new Map();
  async function cached(url) {
    if (!cache.has(url)) cache.set(url,get(url).catch(error => {cache.delete(url); throw error;}));
    return cache.get(url);
  }
  function collection(name) {
    const ds = new C.CustomDataSource(name);
    viewer.dataSources.add(ds);
    return ds;
  }

  const verifiedImagery=await cached(data+"imagery.json").catch(()=>({layers:[]}));
  const contains=(b,p)=>p.lon>=b[0] && p.lon<=b[2] && p.lat>=b[1] && p.lat<=b[3];
  const opticalLayers=new Map();
  const imageryProviders = [
    ...[0,1].map(i=>new C.SingleTileImageryProvider({url:data+`viking/${i}.jpg`,tileWidth:256,tileHeight:256,
      ellipsoid,rectangle:toRect([i*180-180,-90,i*180,90]),credit:"NASA/JPL · Viking / Mars Trek"})),
    wmts("Mars_Viking_MDIM21_ClrMosaic_global_232m","jpg",7,undefined,"NASA/JPL · Viking / Mars Trek"),
  ];
  const imageLayers = addImages(imageryProviders,0);

  const heightCache = new Map();
  try {
    meta = await get(api + "/api/explorer/meta");
    $("connection").textContent = meta.ctx && meta.global_dem ? "CTX and Mars terrain data ready" : meta.ctx ? "Jezero CTX ready; global elevation unavailable" : meta.global_dem ? "Global elevation ready; Jezero CTX unavailable" : "CTX and global elevation unavailable";
    if (meta.global_dem || meta.ctx) {
      viewer.terrainProvider = new C.CustomHeightmapTerrainProvider({
        width:33,height:33,tilingScheme,credit:"NASA PDS MGS/MOLA · USGS MRO/CTX",
        callback:async (x,y,z)=>{
          const level = Math.min(z,17);
          if (z > level) {
            const factor = 2 ** (z-level);
            const parent = await heightBuffer(level, Math.floor(x/factor), Math.floor(y/factor));
            const slice = new Float32Array(33*33);
            for (let row=0;row<33;row++) for(let col=0;col<33;col++) {
              const sy=((y%factor)*32+row)/factor, sx=((x%factor)*32+col)/factor;
              const iy=Math.floor(sy), ix=Math.floor(sx), fx=sx-ix, fy=sy-iy;
              const v=(r,c)=>parent[Math.min(32,r)*33+Math.min(32,c)];
              slice[row*33+col]=(1-fy)*((1-fx)*v(iy,ix)+fx*v(iy,ix+1))+fy*((1-fx)*v(iy+1,ix)+fx*v(iy+1,ix+1));
            }
            return slice;
          }
          return heightBuffer(z,x,y);
        },
      });
    }
  } catch (error) {
    $("connection").textContent = "Could not connect to the data server";
    $("connection").classList.add("status-error");
  }
  async function heightBuffer(z,x,y) {
    const key = `${z}/${x}/${y}`;
    if (!heightCache.has(key)) {
      if (heightCache.size >= 128) heightCache.delete(heightCache.keys().next().value);
      heightCache.set(key,fetch(api+`/api/explorer/terrain/${key}.bin`).then(r=>{
        if (!r.ok) throw new Error("Could not load the elevation tile");
        return r.arrayBuffer();
      }).then(buf=>new Float32Array(buf)).catch(error=>{heightCache.delete(key); throw error;}));
    }
    return heightCache.get(key);
  }

  const localResolution = [meta.global_dem ? `${fmt(meta.global_dem.resolution_m,0)} m MOLA` : "",
    meta.ctx ? "20 m CTX" : "", meta.hirise ? "≈ 1 m HiRISE" : ""].filter(Boolean).join(" · ");
  const catalog = [
    {id:"surface", name:"Surface imagery", author:"NASA/JPL/MSSS/UArizona · Viking, MRO CTX and HiRISE", resolution:"Viking 232 m · global CTX ≈10 m served pixels · regional CTX/HiRISE", unit:"Visible-light imagery", detail:"Verified optical mosaics load automatically by footprint and zoom. Global CTX source is nominally 5 m, but this WMTS stops at level 11 (512-pixel tiles, ≈10 m/pixel at the equator). Missing imagery retains the coarser map; source mosaics may have registration seams.", url:trek, on:true, alpha:1, load:()=>imageLayers},
    {id:"height", name:"Elevation", author:"MGS/MOLA and USGS CTX", resolution:localResolution, unit:"m · areoid", legend:"linear-gradient(90deg,#2d317b,#217099,#3b9a88,#e2b962,#be5733,#fdf2dc)", scale:"−9,000 · 0 · 22,000 m", url:mola, load:()=>addImages([localRaster("height")])},
    {id:"relief", name:"Topographic relief", author:"MGS/MOLA · USGS CTX · HiRISE", resolution:localResolution, unit:"m · areoid", detail:"Elevation colors with DEM-derived hillshade (northwest light, 45° altitude). Brightness is illumination; hue encodes elevation.", url:mola, load:()=>addImages([localRaster("relief")])},
    {id:"slope", name:"Slope", author:"Derived from elevation models", resolution:localResolution, unit:"°", alpha:.58, legend:"linear-gradient(90deg,#235158,#378e88,#eac952,#f79036,#e94b3b,#901737)", scale:"0 · 5 · 10 · 15 · 20 · ≥30°", url:ctx, load:()=>addImages([localRaster("slope")])},
    {id:"roughness", name:"Surface roughness", author:"MOLA / CTX · derived from digital elevation", resolution:localResolution, unit:"m", detail:"Absolute difference between a cell's elevation and the mean of its four neighbors. Compare values at the same resolution.", legend:"linear-gradient(90deg,#193651,#3e7da7,#5bcdba,#e7ce76,#e97650,#fde6b8)", scale:"0 · 0.5 · 2 · 10 · 200 · ≥1,500 m", url:ctx, load:()=>addImages([localRaster("roughness")])},
    {id:"geology", name:"Geology", author:"USGS SIM 3464 / SIM 3292", resolution:"Jezero 1:75,000 · Mars 1:20,000,000", unit:"Geologic map unit", detail:"Colors distinguish map units. The location panel shows the unit code and map scale.", url:jgeo, alpha:.60, load:async()=>loadGeology()},
    {id:"thermal", name:"Thermal inertia · source image", author:"MGS / TES · NASA Mars Trek", resolution:"Source sampling approximately 3 km; WMTS only levels 0–1", unit:"Source colors; numerical legend unavailable", detail:"Physical thermal inertia uses J m⁻² K⁻¹ s⁻½. This colorized WMTS has no verified numeric color key in this app: colors are not temperatures or route risk values.", url:trek, load:()=>addImages([wmts("TES_Thermal_Inertia","png",1)])},
    {id:"ir", name:"Nighttime infrared", author:"Mars Odyssey / THEMIS", resolution:"100 m · approximately ±65°", unit:"Relative infrared image brightness", detail:"Historical mosaic. Light and dark tones show image contrast.", legend:"linear-gradient(90deg,#1a1a1a,#e8e8e8)", url:trek, load:()=>addImages([wmts("THEMIS_NightIR_ControlledMosaics_100m_v2_oct2018","png",9,[-180,-65,180,65])])},
    {id:"temperature", name:"Temperature · MEDA", author:"Perseverance / MEDA ATS", resolution:"One location and time sample in Jezero", unit:"°C", detail:"Select the blue marker to view the archived measurement.", url:meda, load:()=>loadObservations("meda","#7cc8ff")},
    {id:"dust", name:"Dust · historical model", author:"MRO / MCS · Montabone et al.", resolution:"3° × 3° · MY34 Sol 400", unit:"9.3 µm τ · 610 Pa reference", detail:"Atmospheric dust model interpolated from archived observations for the specified sol.", url:dustSource, absent:!meta.dust_available,
      legend:"linear-gradient(90deg,#1c2552,#2f5c97,#41a7ac,#f6bb5e,#f56a36,#992740)", scale:"0 · 0.25 · 0.5 · 1 · 2 · ≥4",
      load:()=>addImages([new C.SingleTileImageryProvider({url:data+"dust-my34-sol400.png",
        tileWidth:720,tileHeight:360,ellipsoid,credit:"Montabone et al. · CC BY-SA 3.0"})])},
    {id:"radiation", name:"Radiation · RAD", author:"Curiosity / RAD E · NASA PDS PPI", resolution:"One archived observation · same-sol rover waypoint", unit:"µGy/h · absorbed dose rate", detail:"Local historical observation, not a global map. The marker uses a same-sol rover endpoint, not exact instrument geometry. No radiation factor is applied to route costs; missing data are unknown.", url:rad, load:()=>loadObservations("radiation","#c5a8f2")},
    {id:"coverage", name:"Elevation data coverage", author:"USGS · CTX and HiRISE cell coverage", resolution:localResolution, unit:"Valid raster cell", detail:"Teal shows CTX coverage and purple shows HiRISE coverage. MOLA provides regional planning data elsewhere.", legend:"linear-gradient(90deg,#2fd8c5 50%,#bc96f6 50%)", url:ctx, load:()=>addImages([localRaster("coverage")])},
    {id:"science", name:"Science sites", author:"NASA/JPL · Perseverance", resolution:"Mission markers with varying location accuracy", unit:"Point", detail:"Select an orange marker to view a science site.", url:"https://science.nasa.gov/mission/mars-2020-perseverance/", on:true, load:()=>loadScience()},
  ];
  for (const layer of catalog) {
    if (["height","relief","slope","roughness","coverage"].includes(layer.id))
      layer.absent=!meta.ctx && !meta.hirise && !meta.global_dem;
    if (["height","relief"].includes(layer.id)) layer.alpha=1;
    if (layer.id==="coverage") layer.scale="Teal: valid CTX cell · purple: valid HiRISE cell · transparent: no local DEM; MOLA may still be available";
    const key=layer.id==="relief"?"height":layer.id;
    const scheme=meta.legends?.[key];
    if (scheme) {
      const first=scheme.values[0],last=scheme.values.at(-1);
      layer.legend=`linear-gradient(90deg,${scheme.colors.map((c,i)=>`${c} ${100*(scheme.values[i]-first)/(last-first)}%`).join(",")})`;
      layer.scale=scheme.values.map(v=>fmt(v,2)).join(" · ")+` ${layer.unit}`;
      if (key==="slope") layer.scale+=" · 15–20° caution; >20° excluded from routing";
      if (key==="height") layer.scale+="; outside endpoints colors saturate";
    }
  }
  const unitColor=unit=>{
    let hash=0;
    for (const c of String(unit)) hash=(hash*31+c.charCodeAt(0))>>>0;
    return `hsl(${hash%360}, ${45+(hash>>>8)%20}%, ${48+(hash>>>16)%16}%)`;
  };

  async function loadGeology() {
    const products = ["global","jezero"].filter(scope=>meta.geology?.[scope]);
    if (!products.length) throw new Error("The geology layer is unavailable.");
    const layers = [];
    for (const scope of products) {
      const geo = await cached(data+`${scope}-geology.geojson`);
      const ds = collection(scope+" geology");
      const color = unitColor;
      const geologyLayer=catalog.find(l=>l.id==="geology");
      geologyLayer.unitLegend ||= {};
      geologyLayer.unitLegend[scope]=[...new Map(geo.features.map(f=>[f.properties.unit,f.properties])).values()];
      ds.entities.suspendEvents();
      for (const f of geo.features) {
        const g=f.geometry;
        if (!g) continue;
        const items = g.type==="Polygon" ? [g.coordinates] : g.coordinates;
        const poly = rings => new C.PolygonHierarchy(rings[0].slice(0,-1).map(([x,y])=>cart(longitude(x),y)),
          rings.slice(1).map(h=>new C.PolygonHierarchy(h.slice(0,-1).map(([x,y])=>cart(longitude(x),y)))));
        const tint = C.Color.fromCssColorString(color(f.properties.unit));
        for (const rings of items) if (rings[0]?.length>3) {
          const entity=ds.entities.add({polygon:{hierarchy:poly(rings),material:tint.withAlpha(.6),zIndex:scope==="jezero"?2:1}});
          entity.layerColor=tint;
        }
      }
      ds.entities.resumeEvents();
      layers.push(ds);
    }
    return layers;
  }
  async function loadObservations(id,color) {
    const ds = collection(id);
    const records = (meta.observations || []).filter(o=>o.id===id);
    if (!records.length) throw new Error("The sample measurement is unavailable.");
    const heights=await get(api+"/api/explorer/heights",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify(records.map(o=>o.point))}).catch(()=>records.map(()=>null));
    records.forEach((o,i)=>marker(ds,{lon:o.point[0],lat:o.point[1],height:heights[i]===null?undefined:heights[i]+3},
      color,id==="meda"?"MEDA":"RAD",()=>observationInfo(o)));
    return [ds];
  }
  async function loadScience() {
    const ds = collection("Science sites");
    const collectionData = await cached("../data/science_points.json");
    for (const f of collectionData.features) {
      const p = f.properties;
      marker(ds,{lon:f.geometry.coordinates[0],lat:f.geometry.coordinates[1]},"#ffab65",p.name,()=>{
        pointLock++;
        const target = $("point-info");
        target.replaceChildren(el("h3",p.name),el("p",p.science_summary),el("p",p.coordinate_accuracy));
        if (/^https:\/\//i.test(p.image_preview_url || "")) {
          const photo=el("img",undefined,"observation-image");
          photo.src=p.image_preview_url;photo.alt=p.image_caption||p.name;
          target.append(photo,el("p",p.image_credit));
        }
        target.append(link("NASA rover photos",p.image_gallery_url));
      });
    }
    return [ds];
  }
  function updateLayer(layer) {
    const show=layer.checkbox.checked;
    const alpha=+layer.slider.value/100;
    for (const item of layer.items || []) {
      item.show=show;
      if (item instanceof C.ImageryLayer) item.alpha=alpha;
      else for (const entity of item.entities.values) {
        if (entity.polygon) entity.polygon.material=entity.layerColor.withAlpha(alpha);
        else if (entity.point) {
          const tint=entity.layerColor || (entity.layerColor=entity.point.color.getValue(viewer.clock.currentTime));
          entity.point.color=tint.withAlpha(alpha);
          if (entity.label) entity.label.show=alpha>0;
        }
      }
    }
    if (layer.id==="geology") updateView();
    if (layer.id==="surface") updateOptical();
    updateLegends();
    $("footer-layer").textContent = catalog.filter(l=>l.checkbox?.checked).map(l=>l.name).join(" · ") || "No layers selected";
    scene.requestRender();
  }
  async function toggleLayer(layer) {
    if (layer.checkbox.checked && !layer.items) {
      layer.status.textContent="Loading…";
      try {
        layer.pending ||= Promise.resolve(layer.load());
        layer.items=await layer.pending;
        layer.status.textContent=layer.id==="radiation"?"Only a local Gale Crater archive record. Use Show archived observation; no radiation coverage elsewhere.":
          layer.id==="temperature"?"Only a local Jezero archive record. Use Show archived observation; no global temperature coverage.":"";
      } catch (error) {
        layer.pending=null;
        layer.checkbox.checked=false;
        layer.status.textContent=error.message;
      }
    }
    updateLayer(layer);
  }
  function updateLegends() {
    const target=$("map-legend");
    target.replaceChildren();
    for (const layer of catalog.filter(l=>l.checkbox?.checked && !["surface","science"].includes(l.id))) {
      const box=el("details");box.open=true;
      box.append(el("summary",layer.name));
      if (layer.legend) {
        const gradient=el("div",undefined,"legend");gradient.style.background=layer.legend;
        box.append(gradient,el("small",layer.scale || layer.unit));
      } else if (layer.id==="geology") {
        box.append(el("small","Display palette; unit names follow USGS maps. Not official map colors."));
        for (const p of layer.unitLegend?.[layer.legendScope || "global"] || []) {
          const row=el("div",undefined,"unit-key"),swatch=el("span");swatch.style.background=unitColor(p.unit);
          row.append(swatch,el("small",`${p.unit} · ${p.name}`));box.append(row);
        }
      } else if (["radiation","temperature"].includes(layer.id)) {
        const id=layer.id==="temperature"?"meda":"radiation";
        const records=(meta.observations || []).filter(o=>o.id===id);
        box.append(el("small",records.length?records.map(o=>`${fmt(o.value,5)} ${o.unit} · ${o.time} · Sol ${o.sol}`).join("; "):"No archived measurement available."));
        box.append(el("p","Colored markers denote local historical observations; no surrounding dose or temperature field is inferred."));
      } else box.append(el("small",layer.detail || layer.unit));
      if (["height","relief","slope","roughness"].includes(layer.id)) box.append(el("p",analysisSource));
      if (layer.slider && +layer.slider.value<100) box.append(el("p",`Opacity ${layer.slider.value}%: display colors blend with underlying layers; the key describes source colors.`));
      if (layer.id==="height" || layer.id==="relief") box.append(el("p",meta.elevation_reference));
      target.append(box);
    }
    target.hidden=!target.children.length;
  }
  function updateOptical() {
    const surface=catalog.find(l=>l.id==="surface");
    if (!surface?.checkbox) return;
    const height=viewer.camera.positionCartographic.height;
    const view=viewer.camera.computeViewRectangle(ellipsoid);
    const box=view && [C.Math.toDegrees(view.west),C.Math.toDegrees(view.south),
                       C.Math.toDegrees(view.east),C.Math.toDegrees(view.north)];
    const products=verifiedImagery.layers || [];
    const selection=opticalSelection(products,height,box);
    const {detail}=selection;
    // A grayscale coarse fallback fills genuine CTX/HiRISE gaps without brown
    // stripes. No detail is synthesized; the far-view Viking colors are retained.
    for (const layer of imageLayers.slice(0,3)) layer.saturation=1-detail;
    const active=[];
    for (const product of products) {
      // A regional image must cover the view: isolated rectangular patches do
      // not stack across the global mosaic at wide zoom levels.
      const visible=selection.active.includes(product);
      if (visible && !opticalLayers.has(product.id)) {
        const provider=new C.UrlTemplateImageryProvider({url:product.template,tilingScheme,
          tileWidth:product.tile_width,tileHeight:product.tile_height,
          maximumLevel:product.max_level,rectangle:toRect(product.bounds),credit:product.attribution,enablePickFeatures:false});
        const [layer]=addImages([provider]);
        opticalLayers.set(product.id,layer);imageLayers.push(layer);
      }
      const layer=opticalLayers.get(product.id);
      if (layer) {
        layer.show=Boolean(visible && surface.checkbox.checked);layer.alpha=detail*+surface.slider.value/100;
        if (layer.show) active.push(product);
      }
    }
    // Keep science overlays above optical imagery; finer products above coarse ones.
    for (const p of [...(verifiedImagery.layers || [])].reverse()) {
      const layer=opticalLayers.get(p.id);
      if (layer) viewer.imageryLayers.lowerToBottom(layer);
    }
    for (const layer of imageLayers.slice(0,3).reverse()) viewer.imageryLayers.lowerToBottom(layer);
    const point=pick(new C.Cartesian2(scene.canvas.clientWidth/2,scene.canvas.clientHeight/2));
    const best=active.filter(p=>point && contains(p.bounds,point)).at(-1);
    $("imagery-status").textContent=best?`${best.instrument} · finest served pixel ≈ ${fmt(best.resolution_m,2)} m at equator. Footprint may contain gaps; actual tile detail varies.`:
      "Viking 232 m color context. Zoom in for CTX/HiRISE; gaps use a coarser grayscale background.";
    if (detail>0) $("imagery-status").textContent+=" Coarser gaps remain grayscale; original mosaic seams can remain.";
  }
  for (const layer of catalog) {
    const row=el("div",undefined,"layer-row");
    const title=el("label",undefined,"layer-title");
    layer.checkbox=el("input"); layer.checkbox.type="checkbox";layer.checkbox.checked=Boolean(layer.on);layer.checkbox.disabled=Boolean(layer.absent);
    title.append(layer.checkbox,el("span",layer.name));
    const details=el("details");
    details.append(el("summary","Source and legend"),el("p",layer.author),el("p",`${layer.resolution} · ${layer.unit}`));
    if (layer.detail) details.append(el("p",layer.detail));
    if (layer.legend) {
      const gradient=el("div",undefined,"legend");gradient.style.background=layer.legend;
      details.append(gradient,el("small",layer.scale));
    }
    details.append(el("br"),link("Data source",layer.url));
    if (["height","slope","roughness","coverage"].includes(layer.id) && meta.hirise)
      details.append(el("br"),link("Jezero HiRISE elevation model",meta.hirise.url));
    layer.slider=el("input");layer.slider.type="range";layer.slider.min=0;layer.slider.max=100;layer.slider.value=Math.round((layer.alpha??.8)*100);
    layer.slider.setAttribute("aria-label",layer.name+" opacity");
    if (!layer.absent) details.append(layer.slider);
    layer.status=el("small",undefined,"missing");
    if (layer.absent) layer.status.textContent="Required local data product is unavailable.";
    row.append(title,details,layer.status);$("layers").append(row);
    if (["radiation","temperature"].includes(layer.id)) {
      const show=el("button","Show archived observation");show.type="button";
      show.onclick=()=>{
        const record=(meta.observations || []).find(o=>o.id===(layer.id==="temperature"?"meda":"radiation"));
        if (!record) {layer.status.textContent="No archived record is installed.";return;}
        layer.checkbox.checked=true;toggleLayer(layer);
        fly({lon:record.point[0],lat:record.point[1]},24000);observationInfo(record);
      };
      row.append(show);
    }
    layer.checkbox.onchange=()=>toggleLayer(layer);
    layer.slider.oninput=()=>updateLayer(layer);
    if (layer.on) toggleLayer(layer);
  }
  for (const [id,label] of Object.entries(factorNames)) {
    const row=el("label",undefined,"check");
    const cb=el("input");cb.type="checkbox";cb.checked=["height","slope","radiation","temperature","dust"].includes(id);
    if (["height","slope"].includes(id)) cb.disabled=true;
    row.append(cb,el("span",label));$("coverage-options").append(row);
    controls[id]=cb;
  }

  const updateView = () => {
    updateOptical();
    const lonlat=pick(new C.Cartesian2(scene.canvas.clientWidth/2,scene.canvas.clientHeight/2));
    const high=viewer.camera.positionCartographic.height;
    const b=meta.ctx_bounds;
    const local=b && lonlat && high<220000 && lonlat.lon>=b[0] && lonlat.lon<=b[2] && lonlat.lat>=b[1] && lonlat.lat<=b[3];
    const fine=meta.hirise_bounds;
    const precise=fine && lonlat && high<10000 && lonlat.lon>=fine[0] && lonlat.lon<=fine[2] && lonlat.lat>=fine[1] && lonlat.lat<=fine[3];
    $("map-mode").textContent=local?"Jezero · 3D":"Mars · 3D";
    $("footer-source").textContent=precise?"3D terrain · HiRISE ≈ 1 m":local?"3D terrain · CTX 20 m":meta.global_dem?`3D terrain · MOLA ${fmt(meta.global_dem.resolution_m,0)} m`:"Mars 2000 · R 3,396.19 km";
    for (const layer of catalog.filter(l=>l.id==="geology")) if (layer.items?.length===2 && layer.checkbox.checked) {
      layer.items[1].show=Boolean(local);
      layer.items[0].show=!local;
      layer.legendScope=local?"jezero":"global";
    }
    updateLegends();
    if (lonlat) {
      const other=pick(new C.Cartesian2(scene.canvas.clientWidth/2+55,scene.canvas.clientHeight/2));
      const length=other ? C.Cartesian3.distance(cart(lonlat.lon,lonlat.lat),cart(other.lon,other.lat)) : 0;
      $("scale").textContent=length ? `55 px ≈ ${length>1000?fmt(length/1000)+" km":fmt(length,0)+" m"}`:"—";
    }
  };
  viewer.camera.moveEnd.addEventListener(updateView);
  let opticalUpdate=0;
  viewer.camera.changed.addEventListener(()=>{
    if (performance.now()-opticalUpdate<150) return;
    opticalUpdate=performance.now();updateOptical();
  });
  updateView();

  function gotoPlace(p) {
    selected.entities.removeById("search-result");
    if (searchMark) selected.entities.remove(searchMark);
    const e=searchMark=marker(selected,p,"#fff2b1",p.name);
    $("search-results").replaceChildren();
    fly(p,p.name==="Jezero"?38000:80000);
    inspect(p);
    e.readInfo=()=>inspect(p);
  }
  let searchMark;
  async function search(showList=true) {
    const input=$("search").value.trim();
    if (!input) { $("search-results").replaceChildren();return; }
    const coords=parseCoords(input);
    if (coords) {
      if (searchMark) selected.entities.remove(searchMark);
      searchMark=marker(selected,coords,"#fff2b1","Search result");
      fly(coords);inspect(coords);$("search-results").replaceChildren();return;
    }
    try {
      const places=await cached(data+"gazetteer.json");
      if ($("search").value.trim()!==input) return;
      const query=input.toLowerCase();
      const options=places.filter(p=>p.name.toLowerCase().includes(query)).sort((a,b)=>
        Number(!a.name.toLowerCase().startsWith(query))-Number(!b.name.toLowerCase().startsWith(query))).slice(0,6);
      if (!showList && options.length) {
        if (searchMark) selected.entities.remove(searchMark);
        gotoPlace(options[0]);return;
      }
      $("search-results").replaceChildren(...options.map(p=>{
        const button=el("button",`${p.name} · ${p.type}`);
        button.type="button";
        button.onclick=()=>{if(searchMark)selected.entities.remove(searchMark);gotoPlace(p);};
        return button;
      }));
      if (!options.length) $("search-results").append(el("p","No matching locations","muted"));
    } catch { $("search-results").textContent="Could not load the place-name index."; }
  }
  $("search-form").onsubmit=e=>{e.preventDefault();search(false);};
  let timer;
  $("search").oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>search(true),170);};

  let roverVersion=0;
  const roverHeights=new Map();
  $("rover").onchange=async()=>{
    const id=$("rover").value, version=++roverVersion;
    mission.entities.removeAll();roverStrokes.length=0;$("rover-info").replaceChildren();scene.requestRender();
    if (!id) return;
    $("rover-info").textContent="Loading mission archive…";
    try {
      const track=await cached(data+id+".geojson");
      if (version!==roverVersion) return;
      const vertices=track.features.flatMap(f=>f.geometry.coordinates);
      if (!roverHeights.has(id)) {
        const values=await get(api+"/api/explorer/heights",{method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify(vertices)}).catch(()=>vertices.map(()=>null));
        roverHeights.set(id,values);
      }
      if (version!==roverVersion) return;
      const [name,url]=roverSources[id];
      const showSegment=f=>{
        pointLock++;
        const target=$("point-info");
        target.replaceChildren(el("h3",name+" · historical traverse"));
        field(target,"Mars sol",f.properties.sol??"Unavailable for this segment");
        target.append(link("Mission archive",url));
      };
      let vertex=0;
      const heights=roverHeights.get(id);
      for (const f of track.features) {
        roverStrokes.push({color:"#f3d37b",width:3,dash:true,alpha:1,readInfo:()=>showSegment(f),
          points:f.geometry.coordinates.map(([lon,lat])=>({surface:cart(lon,lat,1),
            terrain:cart(lon,lat,heights[vertex++] ?? 0)}))});
      }
      const where={lon:track.center[0],lat:track.center[1]};
      marker(mission,where,"#f3d37b",name,()=>showSegment(track.features[Math.floor(track.features.length/2)]));
      $("rover-info").replaceChildren(el("p",`${fmt(track.distance_km,2)} km · from archived tracks`),
        track.sol_range ? el("p",`Sol ${track.sol_range[0]}–${track.sol_range[1]}`):el("p","Sol information is unavailable for this track"),link("Mission archive",url));
      fly(where,18000);
    } catch {
      if (version===roverVersion) $("rover-info").textContent="Could not load the archived traverse.";
    }
  };

  function displayRoutes(result, active) {
    setAnalysisModel(result.source.id,result.source.name);
    planned.entities.removeAll();
    routeStrokes.length=0;
    const cards=$("route-results");
    cards.replaceChildren();
    const coverageLabels={available:"Available",partial:"Partial",missing:"Missing"};
    const selectedFeature=result.features[active];
    result.features.forEach((feature,i)=>{
      const coords=feature.geometry.coordinates,p=feature.properties;
      const tint=routeColors[i%routeColors.length];
      if (i!==active) routeStroke(coords,p.elevations_m,tint,2,false,.8);
      const card=el("article",undefined,"route-card");
      card.setAttribute("aria-current",String(i===active));
      const title=el("button",p.profiles.map(name=>profileNames[name]).join(" / "));
      const dot=el("span",undefined,"route-dot");dot.style.background=tint;title.prepend(dot);
      title.onclick=()=>displayRoutes(result,i);
      card.append(title,el("p",`${fmt(p.distance_km,3)} km · max slope ${fmt(p.max_slope_deg)}° · mean ${fmt(p.mean_slope_deg)}°`));
      if (i===active) {
        field(card,"Descent / ascent",`${fmt(p.descent_m)} / ${fmt(p.ascent_m)} m`);
        field(card,"Estimated walking time",`${fmt(p.estimated_time_hours,2)} h`);
        field(card,"Mean roughness",p.mean_roughness_m===null?null:`${fmt(p.mean_roughness_m,2)} m`);
        field(card,"Steep segments",String(p.hazards.length));
        field(card,"Search grid offset",`${fmt(p.start_snap_m,0)} / ${fmt(p.end_snap_m,0)} m`);
        if (p.source.routing_step_m) field(card,"Routing search step",`${fmt(p.source.routing_step_m/1000,2)} km`);
        if (p.distance_km===0) card.append(el("p","Both endpoints fall in the same elevation cell. Use a finer model for a route at this scale.","caution"));
        if (active>0) {
          const first=result.features[0].properties;
          field(card,"Compared with the first route",`${fmt(p.distance_km-first.distance_km,3)} km / ${fmt(p.mean_slope_deg-first.mean_slope_deg,2)}° mean slope difference`);
        }
        for (const [key,v] of Object.entries(p.coverage)) {
          const label=`${factorNames[key]} · ${coverageLabels[v.status]} (${fmt(v.percent)}%)`;
          const row=el("details",undefined,v.status==="available"?"":"missing");
          row.append(el("summary",label),el("p",v.detail));card.append(row);
        }
        card.append(link(`${p.source.name} · ${fmt(p.source.resolution_m,0)} m`,p.source.url));
      }
      cards.append(card);
    });
    const coords=selectedFeature.geometry.coordinates;
    const props=selectedFeature.properties;
    const pColor=routeColors[active%routeColors.length];
    routeStroke(coords,props.elevations_m,pColor,4);
    const gapSegments=new Set();
    for (const gaps of Object.values(props.gaps)) for (let [from,to] of gaps) {
      if (from===to) {if (to<coords.length-1) to++;else from=Math.max(0,from-1);}
      if (!gapSegments.has(`${from}:${to}`)) routeStroke(coords.slice(from,to+1),props.elevations_m.slice(from,to+1),"#e0c4fb",2,true);
      gapSegments.add(`${from}:${to}`);
    }
    for (const hazard of props.hazards) {
      const [lon,lat]=coords[hazard.at];
      const from=Math.max(0,hazard.from-1), to=Math.min(coords.length-1,hazard.to+1);
      routeStroke(coords.slice(from,to+1),props.elevations_m.slice(from,to+1),"#ff8e58",5);
      marker(planned,{lon,lat},"#ff8e58",null,()=>{
        pointLock++;
        const point=$("point-info");
        point.replaceChildren(el("h3","Steep slope"),el("p",hazard.detail));
        field(point,"Calculated slope",`${fmt(hazard.value)}°`);
        field(point,"Prototype warning threshold",`${fmt(hazard.threshold)}°`);
        field(point,"Location",pointText(lat,lon));
        point.append(link(`${props.source.name} · ${fmt(props.source.resolution_m,0)} m`,props.source.url));
      });
    }
    cards.append(el("p","Orange shows steep segments. Dashed purple shows gaps in selected data.","muted"));
    scene.requestRender();
  }
  $("calculate").onclick=async()=>{
    const s=parseCoords($("start").value),e=parseCoords($("end").value);
    if (!s || !e) { $("route-status").textContent="Enter valid latitude and longitude for both endpoints.";return; }
    const version=++routeVersion;
    setEndpoint("start",s);setEndpoint("end",e);setMode("inspect");
    $("calculate").disabled=true;
    $("route-results").replaceChildren();planned.entities.removeAll();routeStrokes.length=0;scene.requestRender();
    $("route-status").textContent="Calculating candidate routes…";
    try {
      const factors=["slope","roughness"].filter(id=>$("factor-"+id).checked);
      const coverage=Object.keys(controls).filter(id=>controls[id].checked);
      const result=await get(api+"/api/explorer/routes",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({start:s,end:e,factors,coverage})});
      if (version!==routeVersion) return;
      $("route-status").textContent=`${result.features.length} candidate routes · ${result.note}`;
      displayRoutes(result,0);
      const lon=s.lon+longitude(e.lon-s.lon)/2;
      const d=C.Cartesian3.distance(cart(s.lon,s.lat),cart(e.lon,e.lat));
      fly({lat:(s.lat+e.lat)/2,lon:longitude(lon)},Math.max(4400,d*2.5));
    } catch (error) {
      if(version===routeVersion) $("route-status").textContent=error.message;
    } finally {
      if(version===routeVersion) $("calculate").disabled=false;
    }
  };
  $("reset").onclick=()=>{
    setAnalysisModel("auto","Finest available elevation at each point");
    routeVersion++;pointLock++;selected.entities.removeAll();planned.entities.removeAll();searchMark=null;routeStrokes.length=0;
    for(const id of ["start","end"]) { $(id).value="";delete endpoints[id]; }
    $("route-status").textContent=""; $("route-results").replaceChildren();$("calculate").disabled=false;
    setMode("inspect");scene.requestRender();
  };
  function setAnalysisModel(model,source) {
    if (analysisModel===model) return;
    analysisModel=model;analysisSource=source;
    for (const layer of catalog.filter(l=>["height","relief","slope","roughness"].includes(l.id))) {
      for (const item of layer.items || []) viewer.imageryLayers.remove(item,true);
      layer.items=null;layer.pending=null;
      if (layer.checkbox.checked) toggleLayer(layer);
    }
  }
  window.marsExplorer={viewer,meta};
}

run().catch(error=>{
  $("connection").textContent="Could not start the 3D map";
  $("connection").classList.add("status-error");
  feedback(error.message+" · Open 2D Jezero from the top bar.");
  console.error(error);
});
