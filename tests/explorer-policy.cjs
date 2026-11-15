// Pure selection-policy checks with the real product manifest; not browser rendering tests.
const assert=require('node:assert/strict');
const test=require('node:test');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('frontend/explorer.js','utf8').split('async function run()')[0];
const context=vm.createContext({window:{Cesium:{}},location:{port:'5051'},document:{}});
vm.runInContext(source,context);
const products=JSON.parse(fs.readFileSync('data/explorer/imagery.json','utf8')).layers;
const select=(height,box)=>context.opticalSelection(products,height,box);

test('far globe retains original color and has no optical patches',()=>{
  const state=select(8e6,[-180,-90,180,90]);
  assert.equal(state.detail,0);assert.equal(state.active.length,0);
});
test('close fallback is fully grayscale and sparse HiRISE is not drawn at regional zoom',()=>{
  const state=select(44000,[-53,-5,-52,-4]);
  assert.equal(state.detail,1);
  assert(state.active.some(p=>p.instrument==='CTX'));
  assert(!state.active.some(p=>p.id==='HiRISE_Global'));
});
test('zoom blending is bounded and monotonic',()=>{
  const levels=[2e6,1.6e6,1.3e6,1.1e6,900000,600000,1000].map(h=>select(h,null).detail);
  assert(levels.every((v,i)=>v>=0 && v<=1 && (!i || v>=levels[i-1])));
});
test('regional footprints must cover the whole view',()=>{
  const box=[77.1,18.1,77.8,18.8];
  assert(!select(1000,box).active.some(p=>p.bounds[2]-p.bounds[0]<350));
});
test('close Jezero chooses a genuinely finer full-view regional product',()=>{
  const box=[77.39,18.44,77.41,18.46];
  const regional=select(1000,box).active.filter(p=>p.bounds[2]-p.bounds[0]<350);
  assert.equal(regional.length,1);assert(regional[0].resolution_m<1);
});
test('publisher LOD fixes HiRISE native pixel size; invalid matrices are excluded',()=>{
  const hirise=products.find(p=>p.id==='HiRISE_Global');
  assert.equal(hirise.max_level,17);assert.equal(hirise.resolution_m,.16);
  assert(hirise.grid_metadata_url.includes('OnMars/HiRISE/MapServer'));
  assert(!products.some(p=>p.id==='CTX_Ortho_11S291E_6mp_B19_017187_1685'));
});
