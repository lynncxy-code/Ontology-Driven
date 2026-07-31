const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const hierarchy = require('./hierarchy_menu.js');

for (const fileName of ['ontology.html', 'instance.html']) {
    const html = fs.readFileSync(path.join(__dirname, fileName), 'utf8');
    const inlineScripts = Array.from(html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))
        .map(match => match[1])
        .filter(source => source.trim());
    assert.ok(inlineScripts.length, `${fileName} should contain inline JavaScript`);
    for (const source of inlineScripts) new Function(source);
}

assert.deepEqual(hierarchy.normalizePath([' 航空展馆 ', '', '家具']), ['航空展馆', '家具']);
assert.deepEqual(hierarchy.normalizePath('航空展馆\\显示与媒体设备'), ['航空展馆', '显示与媒体设备']);
assert.deepEqual(hierarchy.normalizePath([]), ['未分类']);
assert.equal(hierarchy.leafLabel(['航空展馆', '显示与媒体设备', 'LED屏幕']), 'LED屏幕');

const instances = [
    { id: 'screen-2', display_name: '屏幕 B', object_type_rid: 'type.screen', hierarchy_path: ['航空展馆', 'LED屏幕'] },
    { id: 'screen-1', display_name: '屏幕 A', object_type_rid: 'type.screen', hierarchy_path: ['航空展馆', '显示与媒体设备'] },
    { id: 'screen-3', display_name: '屏幕 C', object_type_rid: 'type.screen', hierarchy_path: ['航空展馆', '显示与媒体设备'] },
    { id: 'sofa-1', display_name: '模块沙发', object_type_rid: 'type.sofa', hierarchy_path: ['航空展馆', '家具'] },
    { id: 'unknown-1', display_name: '待整理', object_type_rid: 'type.unknown' },
];

const instanceGroups = hierarchy.groupInstances(instances);
assert.deepEqual(instanceGroups.map(group => group.fullLabel), [
    '航空展馆 / 家具',
    '航空展馆 / 显示与媒体设备',
    '航空展馆 / LED屏幕',
    '未分类',
].sort((a, b) => {
    if (a === '未分类') return 1;
    if (b === '未分类') return -1;
    return a.localeCompare(b, 'zh-Hans-CN');
}));
assert.deepEqual(
    instanceGroups.find(group => group.fullLabel === '航空展馆 / 显示与媒体设备').items.map(item => item.id),
    ['screen-1', 'screen-3']
);
assert.equal(instanceGroups.find(group => group.fullLabel === '航空展馆 / 显示与媒体设备').label, '显示与媒体设备');

const dominantPaths = hierarchy.dominantPathsByType(instances);
assert.deepEqual(dominantPaths.get('type.screen'), ['航空展馆', '显示与媒体设备']);

const typeGroups = hierarchy.groupObjectTypes([
    { rid: 'type.screen', name: '显示屏幕' },
    { rid: 'type.sofa', name: '模块沙发' },
    { rid: 'type.empty', name: '尚无实例类型' },
], instances);
assert.equal(typeGroups.find(group => group.fullLabel === '航空展馆 / 显示与媒体设备').items[0].rid, 'type.screen');
assert.equal(typeGroups.find(group => group.label === '未分类').items[0].rid, 'type.empty');

const tiedPaths = hierarchy.dominantPathsByType([
    { object_type_rid: 'type.tie', hierarchy_path: ['航空展馆', 'LED屏幕', '主屏幕'] },
    { object_type_rid: 'type.tie', hierarchy_path: ['航空展馆', '显示与媒体设备'] },
]);
assert.deepEqual(tiedPaths.get('type.tie'), ['航空展馆', '显示与媒体设备']);

console.log('hierarchy_menu tests passed');
