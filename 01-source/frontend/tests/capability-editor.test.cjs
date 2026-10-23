// No browser, backend, or business data writes. Exercise the actual inline UI code.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(require('node:path').join(__dirname, '../ontology.html'), 'utf8');
function section(start, end) {
    const from = html.indexOf(start), to = html.indexOf(end, from);
    assert.ok(from >= 0 && to > from, `Missing section: ${start}`);
    return html.slice(from, to);
}
const ctx = {
    ref: value => ({value}), computed: getter => ({get value() {return getter();}}),
    selected: {value: {rid:'isolated-type', injected_interfaces:['I3D_Representable','I3D_Spatial','I3D_Visual','I3D_Behavioral']}},
    pendingInterfaces: {value:new Set()}, pendingRemove: {value:new Set()}, saving:{value:false},
    nextTick: fn => Promise.resolve().then(fn), document:{activeElement:null},
    activeCapabilityTab:{value:'behavioral'}, toast:()=>{}, requests:[],
};
ctx.axios = {post: async (url, data) => {
    ctx.requests.push({url,data});
    const ids = new Set(ctx.selected.value.injected_interfaces);
    if (url.endsWith('/remove')) ids.delete(data.interface_rid);
    else for (const rid of data.interfaces) ids.add(rid);
    ctx.selected.value.injected_interfaces = [...ids];
}};
ctx.loadTypes = async () => {};
vm.createContext(ctx);
vm.runInContext(section('        const capabilityInterfaces =', '        const sortedObjectTypes =')
    + section('        function isInjected(', '        function enterEditMode(')
    + section('        function cancelCapabilityChanges()', '        async function enablePresentationInterface()')
    + '\nconst hasVisual=computed(()=>isInjected("I3D_Visual")); const hasBehavioral=computed(()=>isInjected("I3D_Behavioral"));'
    + '\nglobalThis.testUI={toggleCapability,cancelCapabilityChanges,saveCapabilityChanges,capabilityInterfaces,capabilityChangeCount,capabilityDisabled};',ctx);
(async () => {
    const ui=ctx.testUI;
    assert.ok(ui.capabilityInterfaces.value.some(c=>c.rid==='I3D_Spatial'));
    ui.toggleCapability('I3D_Behavioral');
    assert.ok(ctx.pendingRemove.value.has('I3D_Behavioral'));
    assert.ok(ctx.selected.value.injected_interfaces.includes('I3D_Behavioral'), 'Draft must not modify saved badges');
    ui.cancelCapabilityChanges();
    assert.equal(ui.capabilityChangeCount.value,0);
    ui.toggleCapability('I3D_Representable');
    assert.ok(ctx.pendingRemove.value.has('I3D_Spatial'));
    assert.ok(!ctx.pendingRemove.value.has('I3D_Visual'));
    assert.ok(!ctx.pendingRemove.value.has('I3D_Behavioral'));
    assert.ok(ui.capabilityDisabled('I3D_Spatial'));
    ui.cancelCapabilityChanges();
    ui.toggleCapability('I3D_Behavioral');
    await ui.saveCapabilityChanges();
    assert.equal(ctx.requests.length,1);
    assert.equal(ctx.activeCapabilityTab.value,'visual');
    assert.equal(ui.capabilityChangeCount.value,0);
    ui.toggleCapability('I3D_Behavioral');
    assert.ok(!ctx.selected.value.injected_interfaces.includes('I3D_Behavioral'));
    await ui.saveCapabilityChanges();
    assert.ok(ctx.selected.value.injected_interfaces.includes('I3D_Behavioral'));
    assert.equal(ctx.requests.length,2);
    console.log('PASS: catalog, saved/draft separation, undo, dependency, mocked disable/enable save');
})().catch(e=>{console.error(e);process.exitCode=1;});
