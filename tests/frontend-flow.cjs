// Execute the checked-out frontend sources. Leaflet and HTTP are doubles;
// this verifies application flow, not browser rendering, tiles, or real CORS.
const {execFileSync} = require('node:child_process');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');
const source = name => require('node:fs').readFileSync(require('node:path').join(
 process.env.FRONTEND_SNAPSHOT_DIR || require('node:path').join(__dirname,'../frontend'),name),'utf8');
const config = source('config.js'), app = source('app.js');
function harness(response, failure) {
  const calls=[], drawn=[], removed=[];
  const dom=()=>({style:{},classList:{toggle(){}},append(){},replaceChildren(){}});
  const map={on:(event, fn)=>{if(event==='click')map.click=fn}, removeLayer:l=>removed.push(l), fitBounds:()=>{},getContainer:dom};
  const layer=()=>({addTo(){return this},bindTooltip(){return this},bindPopup(){return this},
    getBounds(){return {}},eachLayer(){return this},addLayer(){}});
  const control=()=>layer(); control.layers=control; control.scale=control;
  const L={extend:Object.assign,featureGroup:layer,CRS:{EPSG4326:{}},map:()=>map,tileLayer:layer,rectangle:layer,
    layerGroup:layer,circleMarker:layer,control,DomEvent:{disableClickPropagation(){}},
    DomUtil:{create:dom},Control:{extend:definition=>class {
      addTo(){this._div=definition.onAdd.call(this);return this}
    }},geoJSON:data=>{drawn.push(data);return layer()}};
  const context=vm.createContext({L,location:{port:'8000'},window:{matchMedia:()=>({matches:false})},document:{createElement:dom,createTextNode:s=>s},TypeError,AbortController,setTimeout,clearTimeout,console,
    fetch:async(url, options)=>{
      if(!options)return {ok:false,status:404};
      calls.push({url,options}); if(failure)throw new TypeError('offline');
      return {ok:response.status===200,status:response.status,json:async()=>response.body};
    }});
  vm.runInContext(config+'\n'+app,context);
  return {context,map,calls,drawn,removed,run:s=>vm.runInContext(s,context)};
}
const good=()=>({type:'Feature',geometry:{type:'LineString',coordinates:[[77.4,18.4],[77.41,18.41]]},
 properties:{distance_km:1,estimated_time_hours:2,max_slope_deg:3}});
test('click sequence, request mapping, route metrics and reset',async()=>{
 const h=harness({status:200,body:good()});
 h.map.click({latlng:{lat:18.4,lng:77.4}}); assert.equal(h.calls.length,0);
 h.map.click({latlng:{lat:18.41,lng:77.41}});
 await new Promise(setImmediate);
 assert.equal(h.calls[0].url,'http://localhost:5000/route');
 assert.equal(h.calls[0].options.method,'POST');
 assert.deepEqual(JSON.parse(h.calls[0].options.body),{
 start:{lat:18.4,lng:77.4,lon:77.4},end:{lat:18.41,lng:77.41,lon:77.41}});
 assert.equal(h.drawn.length,2); assert.match(h.run('routeMetrics({distance_km:1}).distance'),/km/);
 h.map.click({latlng:{lat:18.42,lng:77.42}}); assert.equal(h.removed.length,3);
});
for(const status of [400,422,500,503]) test(`HTTP ${status} does not draw`,async()=>{
 const h=harness({status,body:{error:'test error'}});
 await h.run('requestRoute({lat:18.4,lng:77.4},{lat:18.41,lng:77.41})');
 assert.equal(h.drawn.length,0);assert.match(h.run('statusControl._div.textContent'),/Error: test error/);
});
test('network error is recoverable',async()=>{
 const h=harness(null,true);await h.run('requestRoute({lat:18.4,lng:77.4},{lat:18.41,lng:77.41})');
 assert.equal(h.drawn.length,0);assert.match(h.run('statusControl._div.textContent'),/Could not reach/);
});
test('malformed successful geometry must not reach Leaflet',async()=>{
 const h=harness({status:200,body:{type:'Feature',geometry:{type:'LineString',coordinates:[[77.4,18.4]]}}});
 await h.run('requestRoute({lat:18.4,lng:77.4},{lat:18.41,lng:77.41})');
 assert.equal(h.drawn.length,0);
});
for (const value of [-1, NaN, Infinity, '1', true]) test(`invalid metric ${value} is not displayed as valid`,async()=>{
 const data=good();data.properties.distance_km=value;
 const h=harness({status:200,body:data});
 await h.run('requestRoute({lat:18.4,lng:77.4},{lat:18.41,lng:77.41})');
 // Valid geometry can remain visible if the invalid metric is explicitly marked.
 h.context.metricValue=value;
 assert.equal(h.run('routeMetrics({distance_km:metricValue}).distance'), 'invalid');
});
