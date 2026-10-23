// Execute actual page controller functions with isolated, in-memory API responses.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../instance.html'),'utf8');
function section(a,b){const i=html.indexOf(a),j=html.indexOf(b,i);assert.ok(i>=0&&j>i,a);return html.slice(i,j);}
const snap=()=>({instanceId:'one',objectTypeRid:'type',raw_state:{},interfaces:{I3D_Representable:{is_visible:true},I3D_Visual:{is_visible:true}},runtimeEditor:{spatialEditable:false}});
const ctx={ref:value=>({value}),computed:get=>({get value(){return get();}}),currentSnap:{value:snap()},
 selectedInst:{value:{id:'one'}},objectTypes:{value:[]},overriding:{value:false},
 document:{activeElement:{focus(){}}},nextTick:fn=>fn(),loadModelBinding:async()=>{},selectInstance:()=>{},requests:[]};
ctx.axios={post:async(url,data)=>{ctx.requests.push(data);let result=snap();Object.assign(result.raw_state,data.patch);return {data:{snapshot:result}};},
 get:async()=>({data:snap()})};
vm.createContext(ctx);
vm.runInContext(section('        const overrideFields =','        const activeDatasetLabel =')
 +section('        async function fetchSnap()','        async function openPos()')
 +'\nglobalThis.ui={overridePatch,controlPatch,controlDirtyCount,controlDialog,controlError,controlSavedMessage,snapshotError,snapshotLoading,resetOverride,applyOverride,fetchSnap,closeControlDialog};',ctx);
(async()=>{
 const ui=ctx.ui;
 ui.resetOverride();
 assert.equal(ui.overridePatch.value.runtime_spatial_editable,false,'Snapshot read-only is preserved');
 assert.equal(ui.controlDirtyCount.value,0);
 await ui.applyOverride();
 assert.equal(ctx.requests.length,0,'No-op save makes no request');
 ui.overridePatch.value.is_visible=false;
 assert.equal(ui.controlDirtyCount.value,1);
 ui.resetOverride();
 assert.equal(ui.overridePatch.value.is_visible,true);
 ui.overridePatch.value.animation_state='jump';
 assert.equal(ui.controlDirtyCount.value,0,'Legacy fields cannot enter patch');
 ui.overridePatch.value.is_visible=false;
 await ui.applyOverride();
 assert.equal(JSON.stringify(ctx.requests[0].patch),'{"is_visible":false}','Only changed allowed field is written');
 assert.equal(ui.controlDirtyCount.value,0);
 assert.ok(ui.controlSavedMessage.value.includes('UE'));
 ui.overridePatch.value.is_loaded=false;
 await ui.applyOverride();
 assert.equal(ui.controlDialog.value.kind,'unload');
 assert.equal(ctx.requests.length,1,'Unload awaits explicit confirmation');
 ui.closeControlDialog();
 assert.equal(ui.overridePatch.value.is_loaded,false,'Cancel retains draft');
 ctx.axios.post=async()=>{throw Error('offline');};
 await ui.applyOverride(true);
 assert.equal(ui.controlDirtyCount.value,1);
 assert.ok(ui.controlError.value.includes('修改已保留'));
 ui.resetOverride();
 assert.equal(ui.controlError.value,'');
 ctx.axios.get=async()=>{throw Error('offline');};
 await ui.fetchSnap();
 assert.ok(ui.snapshotError.value);
 assert.equal(ui.snapshotLoading.value,false);
 let respond;
 ctx.axios.get=()=>new Promise(r=>{respond=r;});
 const pending=ui.fetchSnap();
 ctx.selectedInst.value={id:'two'};
 ctx.currentSnap.value=null;
 respond({data:snap()});
 await pending;
 assert.equal(ctx.currentSnap.value,null,'Late snapshot cannot overwrite new selection');
 assert.ok(!html.includes('500MS POLLING'));
 assert.ok(html.includes('role="dialog"'));
 console.log('PASS: baseline, changed-only save, undo, no-op, unload confirmation, failure retention, stale response guard');
})().catch(e=>{console.error(e);process.exitCode=1;});
