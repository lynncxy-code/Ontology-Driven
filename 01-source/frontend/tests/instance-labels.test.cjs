const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../ontology.html'),'utf8');
const start=html.indexOf('        function typeLabelConfig('),end=html.indexOf('        function selectType(',start);
const ctx={ref:value=>({value}),computed:get=>({get value(){return get();}}),
  selected:{value:{rid:'type',interface_configs:{I3D_Overlay:{enabled:true}}}},
  objectTypes:{value:[]},toast:()=>{},requests:[]};
ctx.objectTypes.value=[ctx.selected.value];
ctx.axios={put:async(url,config)=>{ctx.requests.push({url,config});return {data:{label:config}};}};
vm.createContext(ctx);
vm.runInContext(html.slice(start,end)+';globalThis.ui={labelForm,labelDirty,resetLabelForm,saveLabelConfig};',ctx);
(async()=>{
  const ui=ctx.ui;
  assert.equal(ui.labelForm.value.enabled,false);
  ui.labelForm.value.enabled=true;
  ui.labelForm.value.source='fixed';
  ui.labelForm.value.text='hello';
  assert.equal(ui.labelDirty.value,true);
  await ui.saveLabelConfig();
  assert.equal(ui.labelDirty.value,false);
  assert.equal(ctx.selected.value.interface_configs.I3D_Visual.label.text,'hello');
  assert.equal(ctx.selected.value.interface_configs.I3D_Overlay.enabled,true);
  ui.labelForm.value.enabled=false;
  await ui.saveLabelConfig();
  assert.equal(ctx.selected.value.interface_configs.I3D_Visual.label.enabled,false);
  ui.labelForm.value.enabled=true;
  ui.resetLabelForm();
  assert.equal(ui.labelForm.value.enabled,false);
  ctx.selected.value={rid:'another'};
  ui.resetLabelForm();
  assert.equal(ui.labelForm.value.text,'');
  const instance=fs.readFileSync(path.join(__dirname,'../instance.html'),'utf8');
  assert.ok(!instance.includes('@click="overridePatch.animation_state'));
  assert.ok(!instance.includes('@click="overridePatch.material_variant'));
  assert.ok(!instance.includes('@click="overridePatch.fx_trigger'));
  assert.ok(!instance.includes('v-model="overridePatch.ui_label_content"'));
  assert.ok(instance.includes("for (const { key } of overrideFields.value)"));
  console.log('PASS: type label defaults, save, disable, undo, type switch, panel preserved, old controls removed');
})().catch(e=>{console.error(e);process.exitCode=1;});
