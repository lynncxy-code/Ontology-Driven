const assert = require('node:assert/strict');
const { test } = require('node:test');
const { normalize, formatUpdated, pluginRows, render, load } = require('../release-badge.js');

test('one version number worded by the backend; no environment, frontend or backend split', () => {
    const r = normalize({ version: 'rc.25', label: '候选 25', display: 'OntoTwin 候选 25 · 验收版', updated_at: '2026-11-24T02:39:11Z', environment: 'production' });
    assert.equal(r.display, 'OntoTwin 候选 25 · 验收版');
    assert.equal(r.label, '候选 25');
    assert.deepEqual(Object.keys(r).sort(), ['display', 'label', 'updated']);
    assert.equal(normalize({ version: 'rc.9' }).display, 'OntoTwin rc.9');
    assert.equal(normalize(null).display, '版本信息暂不可用');
    assert.equal(normalize({}).updated, '更新时间未记录');
    assert.equal(normalize({ display: 'x'.repeat(500) }).display.length, 120);
});

test('build time is shown with an explicit time zone and never guessed', () => {
    assert.equal(formatUpdated('2026-11-24T02:39:11Z', 'Asia/Shanghai'), '2026-11-24 10:39 UTC+8');
    assert.match(normalize({ updated_at: '2026-11-24T02:39:11Z' }).updated, /^更新于 2026-11-2[34] \d\d:39 UTC/);
    for (const value of [null, '', 'not-a-date', '2026-10-23 14:51:00']) assert.equal(formatUpdated(value), '');
    assert.equal(formatUpdated('2026-11-24T02:39:11Z', 'invalid/zone'), '');
});

test('UE plugin rows say plainly whether each project runs the same version', () => {
    assert.equal(pluginRows(null), null);
    assert.equal(pluginRows({ error: 'auth_required' }), null);
    const rows = pluginRows({ items: [
        { ue_project_name: '展馆', scene_name: 'B', status: 'different', plugin_label: '候选 24' },
        { ue_project_name: '旧工程', scene_name: 'C', status: 'unknown' },
        { ue_project_name: '办公室', scene_name: 'A', status: 'same' },
    ] });
    assert.deepEqual(rows.map(r => r.tone), ['warn', 'muted', 'ok']);
    assert.equal(rows[0].name, '展馆 · B');
    assert.equal(rows[0].status, '不是同一版（插件为 候选 24），请重新安装插件');
    assert.equal(rows[2].status, '同一版');
});

function fakeDocument() {
    const make = tag => ({ tag, className: '', children: [], _text: '',
        appendChild(child) { this.children.push(child); return child; },
        set textContent(v) { this._text = v; this.children = []; },
        get textContent() { return this._text + this.children.map(c => c.textContent).join(''); } });
    return { createElement: make };
}

test('render writes text only and hides the UE block when not signed in', () => {
    const doc = fakeDocument();
    const box = doc.createElement('div');
    render(doc, box, { release: normalize({ display: 'OntoTwin 候选 25 · 验收版' }), plugins: null });
    assert.equal(box.children.length, 2);
    render(doc, box, { release: normalize({ display: '<b>x</b>' }), plugins: [] });
    assert.match(box.textContent, /<b>x<\/b>.*UE 插件最近 7 天没有 UE 工程连过后台/);
    assert.doesNotMatch(box.textContent, /NEW-|BUG-|OPT-/);
});

test('load asks the public release info and the signed-in plugin list', async () => {
    const seen = [];
    const fetcher = async url => { seen.push(url); return url === '/release-info.json'
        ? { ok: true, json: async () => ({ display: 'OntoTwin 候选 25 · 验收版' }) }
        : { ok: false, json: async () => ({}) }; };
    const state = await load(fetcher);
    assert.deepEqual(seen.sort(), ['/api/v4.8/release/ue-plugins', '/release-info.json']);
    assert.equal(state.release.display, 'OntoTwin 候选 25 · 验收版');
    assert.equal(state.plugins, null);
});
