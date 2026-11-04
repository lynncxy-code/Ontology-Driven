const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const html = fs.readFileSync(path.join(__dirname, '../coord_workbench.html'), 'utf8');
function section(start, end) {
  const a=html.indexOf(start), b=html.indexOf(end,a+start.length);
  assert.ok(a>=0 && b>a, start); return html.slice(a,b);
}
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};}
const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
function harness(){
  const elements = new Map();
  const element=id=>{if(!elements.has(id))elements.set(id,{value:id==='cadFrameSelect'?'frame-A':'',textContent:'',innerHTML:'',style:{},disabled:false,appendChild(){},click(){}});return elements.get(id);};
  const c={console,State:{mode:'dxf',cadFrameId:'frame-A',previewData:null,currentStep:1},FloorConfig:{projectId:'project-A'},
    document:{getElementById:element,querySelector:()=>element('upload'),createElement:()=>({})},FormData:class{append(){}},File:class{constructor(_,name){this.name=name}},
    applyPreviewData(){c.applied++},applied:0,toasts:[],toast:(...x)=>c.toasts.push(x),escapeHTML:x=>String(x),
    LAYER_COLORS:{},MOCK_PREVIEW:{name:'mock',layers:[]},cadSnapshotController:null,
    cadAdoptFrame(frame){c.State.cadFrameId=frame.id;c.State.cadSavedOrigin=[0,0];c.State.cadSavedDisplay={};c.adopted=frame.id},
    cadMetricsFromFrame:()=>null,setDisplayOrient(){},renderAnchorList(){},draw(){},scheduleSave(){},
    fetchTypeScanForFrame:async()=>{c.scans++},scans:0,
    cadSyncFrameForm(){},floorConfigSync(){},cadRenderPersistStatus(){},renderLayerList(){},
    UI:{confirm:async()=>true},renderAuditList(){},adoptTypeScanResult(data){c.scanAdopted=data},refreshAssetCatalogForTarget:async()=>{}};
  vm.createContext(c);
  const helpers=html.includes('let cadRequestEpoch')?section('let cadRequestEpoch','async function cadRefreshFrameList('):'';
  vm.runInContext(helpers+section('async function cadParseFile(', 'async function cadCreateFrameAsset(')
    +section('async function cadLoadSelectedFrame(', 'async function cadSaveFrameDraft(')
    +section('async function loadSavedComponents()', 'function highlightTableRow('),c);
  c.el=element;return c;
}
function uploadHarness(){
  const c=harness();
  vm.runInContext(section('async function cadRefreshFrameList(', 'function cadAdoptFrame(')
    +section('async function cadCreateFrameAsset(', 'async function cadLoadSelectedFrame('),c);
  return c;
}
const preview=name=>({name,layers:[{name,color:'#fff'}]});
const response=data=>({ok:true,json:async()=>data});
for(const change of ['project','frame','mode'])test('late preview ignored after '+change+' change',async()=>{
  const c=harness(),d=deferred();c.fetch=()=>d.promise;
  const pending=c.cadParseFile({name:'old'});
  if(change==='project')c.FloorConfig.projectId='project-B';
  if(change==='frame')c.State.cadFrameId='frame-B';
  if(change==='mode')c.State.mode='image';
  d.resolve(response(preview('old')));
  assert.equal(await pending,false);assert.equal(c.State.previewData,null);assert.equal(c.applied,0);
});
test('preview guard also runs after delayed body decoding',async()=>{
  const c=harness(),body=deferred();c.fetch=async()=>({ok:true,json:()=>body.promise});
  const pending=c.cadParseFile({name:'old'});await tick();c.FloorConfig.projectId='B';body.resolve(preview('old'));
  assert.equal(await pending,false);assert.equal(c.applied,0);
});
test('latest preview wins even when frame and project are unchanged',async()=>{
  const c=harness(),a=deferred(),b=deferred();let n=0;c.fetch=()=>++n===1?a.promise:b.promise;
  const old=c.cadParseFile({}),latest=c.cadParseFile({});b.resolve(response(preview('latest')));assert.equal(await latest,true);
  a.resolve(response(preview('old')));assert.equal(await old,false);assert.equal(c.State.previewData.name,'latest');assert.equal(c.applied,1);
});
test('stale preview failure neither throws nor installs mock preview',async()=>{
  for(const allowMock of [false,true]){const c=harness(),d=deferred();c.fetch=()=>d.promise;const p=c.cadParseFile({},allowMock);
    c.State.cadFrameId='B';d.reject(Error('old failure'));assert.equal(await p,false);assert.equal(c.applied,0);}
});
test('active preview failure remains visible to its caller',async()=>{
  const c=harness();c.fetch=async()=>{throw Error('current failure')};await assert.rejects(c.cadParseFile({}),/current failure/);
});
test('context epoch rejects A to B to A and reset results',async()=>{
  const c=harness(),d=deferred();c.fetch=()=>d.promise;const p=c.cadParseFile({});
  if(c.invalidateCadRequests)c.invalidateCadRequests();d.resolve(response(preview('old')));
  assert.equal(await p,false);assert.equal(c.applied,0);
});
for(const result of ['success','failure'])test('stale components '+result+' cannot overwrite current panel',async()=>{
  const c=harness(),d=deferred();c.fetch=()=>d.promise;const p=c.loadSavedComponents();c.State.cadFrameId='B';
  c.el('savedComponentsPanel').textContent='B stays';c.el('savedComponentsPanel').innerHTML='B content';
  if(result==='failure')d.reject(Error('old error'));else d.resolve(response({project_id:'project-A',frame_id:'frame-A',components:[{type_name:'OLD'}]}));
  await p;assert.equal(c.el('savedComponentsPanel').textContent,'B stays');assert.equal(c.el('savedComponentsPanel').innerHTML,'B content');
});
test('latest component request wins; valid rows still render',async()=>{
  const c=harness(),a=deferred(),b=deferred();let n=0;c.fetch=()=>++n===1?a.promise:b.promise;
  const old=c.loadSavedComponents(),latest=c.loadSavedComponents();
  b.resolve(response({project_id:'project-A',frame_id:'frame-A',components:[{type_name:'NEW',ue_xy:[1,2]}]}));await latest;
  a.resolve(response({project_id:'project-A',frame_id:'frame-A',components:[]}));await old;
  assert.ok(c.el('savedComponentsPanel').innerHTML.includes('NEW'));assert.equal(c.el('savedComponentsPanel').textContent,'加载中…');
});
test('mismatched response frame is rejected',async()=>{
  const c=harness();c.fetch=async()=>response({project_id:'project-A',frame_id:'wrong',components:[{type_name:'WRONG'}]});await c.loadSavedComponents();
  assert.ok(!c.el('savedComponentsPanel').innerHTML.includes('WRONG'));assert.match(c.el('savedComponentsPanel').textContent,/失败/);
});
test('saved metadata displays before source download; stale source never starts parsing',async()=>{
  const c=harness(),source=deferred();const urls=[];c.fetch=async url=>{urls.push(url);if(url.endsWith('/source'))return source.promise;return response({id:'frame-A',anchors:[]});};
  const pending=c.cadLoadSelectedFrame();await tick();assert.equal(c.adopted,'frame-A');
  c.el('cadFrameSelect').value='frame-B';source.resolve({ok:true,blob:async()=>({})});await pending;
  assert.ok(!urls.includes('/api/v2/coord/preview'));assert.equal(c.applied,0);assert.equal(c.scans,0);
});
test('out-of-order frame metadata cannot replace newer frame or its loading button',async()=>{
  const c=harness(),a=deferred(),b=deferred();let n=0;c.fetch=()=>++n===1?a.promise:b.promise;
  const old=c.cadLoadSelectedFrame();c.el('cadFrameSelect').value='frame-B';const latest=c.cadLoadSelectedFrame();
  a.resolve(response({id:'frame-A',anchors:[]}));await old;assert.notEqual(c.adopted,'frame-A');assert.equal(c.el('cadLoadFrameBtn').disabled,true);
  b.reject(Error('current error'));await latest;assert.equal(c.el('cadLoadFrameBtn').disabled,false);assert.equal(c.toasts.length,1);
});
test('stale upload failure cannot clear a newer preview or show an error',async()=>{
  const c=uploadHarness(),d=deferred();c.fetch=()=>d.promise;
  const pending=c.handleUpload({target:{files:[{name:'old.dxf'}]}});
  c.invalidateCadRequests();c.State.previewData=preview('current');c.State.cadFrameId='frame-B';
  d.reject(Error('old failure'));await pending;
  assert.equal(c.State.previewData.name,'current');assert.equal(c.toasts.length,0);assert.equal(c.scans,0);
});
test('late created draft cannot adopt its frame into a different project',async()=>{
  const c=uploadHarness(),d=deferred();c.fetch=()=>d.promise;
  const pending=c.cadCreateFrameAsset({name:'old.dxf'});c.FloorConfig.projectId='project-B';
  d.resolve(response({frame:{id:'old'}}));assert.equal(await pending,null);assert.equal(c.adopted,undefined);assert.equal(c.toasts.length,0);
});
test('latest frame list wins and selecting a frame invalidates pending preview',async()=>{
  const c=uploadHarness(),a=deferred(),b=deferred(),previewBody=deferred();let n=0;
  c.fetch=()=>++n===1?a.promise:n===2?b.promise:previewBody.promise;
  const old=c.cadRefreshFrameList('old'),latest=c.cadRefreshFrameList('latest');
  b.resolve(response({frames:[{id:'latest'}]}));await latest;
  a.resolve(response({frames:[{id:'old'}]}));await old;assert.equal(c.el('cadFrameSelect').value,'latest');
  const pending=c.cadParseFile({});c.el('cadFrameSelect').value='other';c.el('cadFrameSelect').onchange();
  previewBody.resolve(response(preview('old')));assert.equal(await pending,false);assert.equal(c.applied,0);
});
test('changing frame while replacement confirmation is open prevents upload',async()=>{
  const c=uploadHarness(),confirm=deferred();let fetches=0;
  c.fetch=async()=>{fetches++;return response({id:'frame-A',name:'A'})};c.UI.confirm=()=>confirm.promise;
  c.cadChooseReplacement();const pending=c.cadReplaceSource({target:{files:[{name:'replacement.dxf'}]}});await tick();
  c.el('cadFrameSelect').value='B';c.invalidateCadRequests();confirm.resolve(true);await pending;
  assert.equal(fetches,1);assert.equal(c.toasts.length,0);
});
for(const failure of [false,true])test('type scan ignores stale '+(failure?'failure':'success')+' after context reset',async()=>{
  const c=harness(),d=deferred();
  vm.runInContext(section('async function fetchTypeScanForFrame(', '// 兼容旧调用方'),c);
  c.fetch=()=>d.promise;const pending=c.fetchTypeScanForFrame('frame-A');c.invalidateCadRequests();
  c.State.scanStatus='current';if(failure)d.reject(Error('old failure'));else d.resolve(response({result:{old:true}}));
  assert.equal(await pending,null);assert.equal(c.scanAdopted,undefined);assert.equal(c.State.scanStatus,'current');
});
test('type results render before catalogue completes and survive catalogue failure',async()=>{
  const c=harness(),catalogue=deferred();let rendered=0;
  vm.runInContext(section('async function fetchTypeScanForFrame(', '// 兼容旧调用方'),c);
  c.State.currentStep=2;
  c.renderAuditList=()=>{if(c.scanAdopted)rendered++};
  c.fetch=async()=>response({result:{candidates:[{block_name:'设备A'}]}});
  c.refreshAssetCatalogForTarget=()=>catalogue.promise;
  const pending=c.fetchTypeScanForFrame('frame-A');await tick();
  assert.equal(rendered,1);
  catalogue.reject(Error('catalogue unavailable'));
  assert.ok(await pending);
  assert.equal(c.scanAdopted.candidates[0].block_name,'设备A');
  assert.notEqual(c.State.scanStatus,'failed');
});
for(const rotation of [0,45,90,180,270])for(const flip of [false,true])test(`CAD fit rotation ${rotation}, mirror ${flip}`,()=>{
  const c={window:{},console,State:{mode:'dxf',previewData:{bounds:{min:[150,-200],max:[10150,800]}}},canvas:{width:2000,height:1200},devicePixelRatio:2,draw(){},updateCanvasInfo(){}};
  vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../spatial_canvas.js'),'utf8'),c);
  c.SpatialCanvas=c.window.OntoTwinSpatialCanvas;c.DisplayM=c.SpatialCanvas.buildDisplayMatrix({rotation_deg:rotation,flip});
  vm.runInContext(section('function fitView()', 'function zoomCanvas('),c);c.fitView();
  assert.equal(c.camX,5150);assert.equal(c.camY,300);
  for(const p of [[150,-200],[150,800],[10150,-200],[10150,800]]){
    const [x,y]=c.SpatialCanvas.worldToScreen(p,{displayMatrix:c.DisplayM,scale:c.camScale,cameraX:c.camX,cameraY:c.camY,canvasWidth:1000,canvasHeight:600});
    assert.ok(x>=0&&x<=1000&&y>=0&&y<=600,`corner outside canvas: ${x},${y}`);
  }
});
