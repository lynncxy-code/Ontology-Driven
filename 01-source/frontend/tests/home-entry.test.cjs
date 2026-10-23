const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const html = fs.readFileSync(path.resolve(__dirname, '../index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
test('old home has only a Nexus fallback, no demo controls, polling or CDN', () => {
    assert.match(html, /http-equiv="refresh" content="0; url=\/nexus"/);
    assert.match(html, /href="\/nexus"/);
    assert.doesNotMatch(html, /vehicle_01|equipment_01|tooling_01|\/api\/|axios|Vue|setInterval|<script[^>]+src=/);
});
test('entry replaces browser history and preserves query/hash on the same origin', () => {
    for (const [search, hash] of [['', ''], ['?page=ontology', '#overview'], ['?next=https://example.com', '']]) {
        const destinations = [];
        vm.runInNewContext(script, { window: { location: { search, hash, replace: value => destinations.push(value) } } });
        assert.deepEqual(destinations, ['/nexus' + search + hash]);
    }
});
