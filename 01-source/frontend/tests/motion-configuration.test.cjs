const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict'), path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../ontology.html'),'utf8');
function section(start,end){const i=html.indexOf(start),j=html.indexOf(end,i);assert.ok(i>=0&&j>i);return html.slice(i,j);}
const ctx={presentationSelections:{value:{channels:{}}},behaviorResources:{value:[]},behaviorSyncState:{value:'saved'}};
vm.createContext(ctx);
vm.runInContext(section('        function normalizeBehaviorResource(', '        async function loadBehaviorResources(')
    +section('        function createPresentationSelections(', '        const assetTotalPages =')
    +section('        function behaviorEntryKey(', '        const presentationProfileSummary =')
    +'\nglobalThis.api={normalizeBehaviorResource,selectBehaviorResource,setBehaviorParameter,buildPresentationProfile,createPresentationSelections,selectBehaviorSource,clearBehaviorSelection,defaultCapabilityTab};',ctx);
const resource=ctx.api.normalizeBehaviorResource({resource_id:'ot.motion.rotate',source:'ontotwin_common',channel:'animation',parameter_schema:[{key:'speed',type:'number',default:90},{key:'axis',type:'select',default:'z'}]});
ctx.behaviorResources.value=[resource];
ctx.api.selectBehaviorResource('status','normal','animation',resource);
ctx.api.setBehaviorParameter('status','normal','animation',resource.parameterSchema[0],'120');
let profile=ctx.api.buildPresentationProfile();
assert.equal(profile.channels.animation.states['status:normal'].params.speed,120);
ctx.presentationSelections.value=ctx.api.createPresentationSelections(profile);
assert.equal(ctx.api.buildPresentationProfile().channels.animation.states['status:normal'].params.speed,120);
ctx.api.selectBehaviorResource('status','normal','animation',resource);
assert.equal(ctx.api.buildPresentationProfile().channels.animation.states['status:normal'].params.speed,120,'Repeated card selection preserves edits');
ctx.api.selectBehaviorSource('status','normal','animation','project');
assert.equal(Object.keys(ctx.api.buildPresentationProfile().channels).length,0);
ctx.api.selectBehaviorResource('status','normal','animation',resource);
ctx.api.selectBehaviorResource('status','fault','animation',resource);
ctx.api.selectBehaviorSource('status','normal','animation','ontotwin_common');
assert.equal(ctx.api.buildPresentationProfile().channels.animation.states['status:normal'].resource_id,resource.id,'Clicking selected source is not a hidden clear');
ctx.api.clearBehaviorSelection('status','normal','animation');
profile=ctx.api.buildPresentationProfile();
assert.equal(profile.behavior_library,'none');
assert.equal(profile.channels.animation.states['status:normal'],undefined);
assert.ok(profile.channels.animation.states['status:fault'],'Other state is preserved');
ctx.presentationSelections.value=ctx.api.createPresentationSelections(profile);
assert.equal(ctx.api.buildPresentationProfile().channels.animation.states['status:normal'],undefined,'Reload stays clear');
ctx.api.clearBehaviorSelection('status','fault','animation');
assert.equal(Object.keys(ctx.api.buildPresentationProfile().channels).length,0);
assert.equal(ctx.api.defaultCapabilityTab(['I3D_Representable','I3D_Behavioral']),'model');
assert.equal(ctx.api.defaultCapabilityTab(['I3D_Representable']),'model');
assert.equal(ctx.api.defaultCapabilityTab(['I3D_Visual']),'visual');
assert.equal(ctx.api.defaultCapabilityTab(['I3D_Behavioral']),'behavioral');
assert.ok(html.includes('v-if="hasRepresentable && activeCapabilityTab === \'model\'"'));
console.log('PASS: motion parameter defaults, edit, serialization, reload and source switch');
