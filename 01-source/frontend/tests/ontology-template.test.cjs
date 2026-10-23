const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
for (const page of ['ontology.html', 'instance.html']) {
const html = fs.readFileSync(path.join(root, page), 'utf8');
for (const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
    if (!m[1].trim()) continue;
    if (m[0].includes('type="importmap"')) JSON.parse(m[1]);
    else if (!m[0].includes('type="module"')) new vm.Script(m[1]);
}
const context = {console};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'vendor/vue-3.3.4.global.prod.js'), 'utf8'), context);
const start = html.indexOf('<div id="app"');
assert.ok(start >= 0);
context.Vue.compile(html.slice(start, html.lastIndexOf('<script>')), {
    decodeEntities: text => text.replace(/&(lt|gt|amp|quot|apos|#39);/g, (_, name) => ({lt:'<',gt:'>',amp:'&',quot:'"',apos:"'",'#39':"'"})[name]),
});
console.log('PASS: ' + page + ' inline JavaScript syntax and Vue template compilation');
}
