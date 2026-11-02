// BUG-17: exercise the restored page's rendering, navigation and status refresh.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../workspace48.html'), 'utf8');
const inline = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).find(s => s.includes('loadProjects'));
new vm.Script(inline);
function runtime(items = []) {
  const elements = {'#projects': {innerHTML: '', contains: () => false}, '#error': {textContent: ''}};
  const calls = [];
  const values = new Map([['ontotwin_project_id', 'web-project']]);
  const context = {
    $, elements, calls, items, location: {},
    document: {hidden: false, activeElement: null, querySelector: () => null},
    sessionStorage: {getItem: k => values.get(k), setItem: (k, v) => values.set(k, v)},
    api: async (url, options) => {calls.push([url, options]);return {items, current_project_id:'other-user-project'};},
  };
  function $(s) {return elements[s];}
  vm.createContext(context);
  // Execute production functions with a small DOM/API adapter, without running unrelated modals.
  const render = inline.slice(inline.indexOf('async function loadProjects()'), inline.indexOf('async function createEmpty()'));
  const refresh = inline.slice(inline.indexOf('let refreshing = false;'), inline.indexOf('setInterval(refreshProjects'));
  vm.runInContext(`const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    let context={org:{organization_id:'org'},factory:{factory_id:'factory'}};
    ${render}\n${refresh}`, context);
  return context;
}
test('accepted workspace structure and explicit binding remain together', () => {
  for (const marker of ['class="factory-panel"', 'class="workspace-body"', 'id="backFactory"', 'id="logoutGlobal"', '/scene_binding.js']) assert.ok(html.includes(marker), marker);
  assert.ok(!html.includes('进入并激活'));
});
test('project cards escape names and show binding, live state and this tab selection', async () => {
  const r=runtime([{project_id:'web-project',name:'<img onerror=x>',ue_project_name:'Plant',scene_name:'Level A',ue_online:true,type_count:2,instance_count:3}]);
  await r.loadProjects();
  const rendered=r.elements['#projects'].innerHTML;
  for(const value of ['&lt;img onerror=x&gt;','已绑定 Plant / Level A','关卡在线','当前项目','关卡绑定','导出','回退','进入项目']) assert.ok(rendered.includes(value),value);
  assert.ok(!rendered.includes('<img'));
});
test('entering a dataset changes only the browser context', async () => {
  const r=runtime(); await r.enter('chosen');
  assert.equal(r.calls.length,1);
  assert.equal(r.calls[0][0],'/context');
  assert.equal(JSON.parse(r.calls[0][1].body).project_id,'chosen');
  assert.equal(r.location.href,'/nexus?nexus=true');
});
test('periodic refresh catches errors, retries and avoids hidden or modal pages', async () => {
  const r=runtime();
  r.api=async()=>{throw Error('offline')};
  await r.refreshProjects(); assert.match(r.elements['#error'].textContent,/offline/);
  let count=0; r.api=async()=>{count++;return {items:[]}};
  await r.refreshProjects(); assert.equal(count,1); assert.equal(r.elements['#error'].textContent,'');
  r.document.hidden=true; await r.refreshProjects(); assert.equal(count,1);
  r.document.hidden=false; r.document.querySelector=()=>({}); await r.refreshProjects(); assert.equal(count,1);
});
