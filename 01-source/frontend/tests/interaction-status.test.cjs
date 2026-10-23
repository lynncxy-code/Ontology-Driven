const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const html = fs.readFileSync(path.join(__dirname, '../interaction.html'), 'utf8');
const runtime = { console };
vm.createContext(runtime);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../vendor/vue-3.3.4.global.prod.js'), 'utf8'), runtime);
const templates = [...html.matchAll(/<span class="row-status"[\s\S]*?<\/span>/g)].map(match => match[0]);
assert.equal(templates.length, 2);

function collect(node, predicate) {
    if (!node || typeof node !== 'object') return [];
    return [ ...(predicate(node) ? [node] : []),
        ...(Array.isArray(node.children) ? node.children.flatMap(child => collect(child, predicate)) : []) ];
}

function check(template, item, label, positive) {
    const node = runtime.Vue.compile(template)({ item }, []);
    const text = collect(node, child => typeof child.children === 'string').map(child => child.children).join('');
    assert.equal(text.trim(), label);
    assert.equal(node.props.class.includes('is-positive'), positive);
    assert.equal(collect(node, child => child.type === (positive ? 'path' : 'circle')).length, 1);
    assert.equal(collect(node, child => child.type === 'svg')[0].props['aria-hidden'], 'true');
}

check(templates[0], { injected_interfaces: ['I3D_Overlay'] }, '已挂载', true);
check(templates[0], { injected_interfaces: [] }, '未挂载', false);
check(templates[1], { online: true }, '在线', true);
check(templates[1], { online: false }, '离线', false);
assert.match(html, /:aria-label="item\.display_name/);
assert.match(html, /\.row-status\{[^}]*flex:none/);

for (const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) {
    if (script[1].trim()) new vm.Script(script[1]);
}
console.log('PASS: four status labels, distinct icons, instance accessible names, fixed badge sizing, inline JS syntax');
