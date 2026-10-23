const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const snapshot=require('../calibration_snapshot.js');
// Header-only PNG is sufficient for the pure validator; browser acceptance also decodes a real PNG.
function fixture() {
  const png=Buffer.alloc(33);
  Buffer.from([137,80,78,71,13,10,26,10]).copy(png);
  png.writeUInt32BE(13,8);png.write('IHDR',12);png.writeUInt32BE(200,16);png.writeUInt32BE(200,20);
  return {schema:'ontotwin.calibration-snapshot',version:1,units:'cm',snapshot_id:'abc123',
    source:{project_name:'QA',ue_project_id:'ue-a',level:'/Game/QA'},
    image:{width:200,height:200,mime_type:'image/png',data_base64:png.toString('base64')},
    points:[
      {id:'P1',ue_world_cm:[0,0,10],image_xy:[10,10]},
      {id:'P2',ue_world_cm:[100,0,10],image_xy:[100,10]},
      {id:'P3',ue_world_cm:[0,100,10],image_xy:[10,100]}]};
}
const valid=fixture();
assert.equal(snapshot.validate(valid),valid);
const mutations=[
  d=>d.units='mm',d=>d.version=2,d=>d.points[1].id='P1',
  d=>d.points[1].ue_world_cm[0]=NaN,d=>d.points[1].ue_world_cm[0]='100',
  d=>d.points[2].ue_world_cm=[200,0,10],d=>d.points[2].ue_world_cm[2]=100,
  d=>d.points[2].ue_world_cm=[200,0.01,10],
  d=>d.points[0].image_xy=[999,0],d=>d.image.width=300,
  d=>d.image.mime_type='image/svg+xml',d=>d.source.level='',d=>d.points=[],
  d=>d.points[0].id='<script>'
];
for(const mutate of mutations){const bad=fixture();mutate(bad);assert.throws(()=>snapshot.validate(bad));}
assert.throws(()=>snapshot.checkSource(valid,{ueProjectId:'ue-b'}),/其他 UE/);
assert.throws(()=>snapshot.checkSource(valid,{level:'/Game/Other'}),/关卡/);
assert.doesNotThrow(()=>snapshot.checkSource(valid,{ueProjectId:'ue-a',level:'/Game/QA'}));
assert.doesNotThrow(()=>snapshot.checkSource(valid,{ueProjectId:'ue-a',level:' /Game/QA '}));
assert.throws(()=>snapshot.anchors(valid,{P1:[0,0],P2:[100,0]}),/P3/);
assert.throws(()=>snapshot.anchors(valid,{P1:[0,0],P2:[100,0],P3:[200,0]}),/共线/);
const before=JSON.stringify(valid);
const anchors=snapshot.anchors(valid,{P1:[1000,2000],P2:[2000,2000],P3:[1000,3000]});
assert.equal(JSON.stringify(valid),before);
const ctx={};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../coord_transform.js'),'utf8')+';this.transform=CoordTransform;',ctx);
const fitted=ctx.transform.calibrate(anchors.map(a=>a.cadXY),anchors.map(a=>a.readings.ue));
const check=ctx.transform.applyTransform(fitted.matrix,[1500,2500]);
assert.ok(Math.abs(check[0]-50)<0.01&&Math.abs(check[1]-50)<0.01);
console.log('PASS: snapshot validation, source isolation, complete pairing, noncollinearity, unchanged input, existing calibration fit');
