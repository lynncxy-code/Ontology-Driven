const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const hierarchy = require('./hierarchy_menu.js');

for (const fileName of ['ontology.html', 'instance.html', 'interaction.html']) {
    const html = fs.readFileSync(path.join(__dirname, fileName), 'utf8');
    const inlineScripts = Array.from(html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))
        .map(match => match[1])
        .filter(source => source.trim());
    assert.ok(inlineScripts.length, `${fileName} should contain inline JavaScript`);
    for (const source of inlineScripts) new Function(source);
}

const instanceHtml = fs.readFileSync(path.join(__dirname, 'instance.html'), 'utf8');
assert.equal((instanceHtml.match(/id="instance-tab-/g) || []).length, 3);
assert.doesNotMatch(instanceHtml, /id="instance-tab-model"/);
assert.match(instanceHtml, /const activeMonitorTab = ref\('control'\)/);
assert.match(instanceHtml, /function selectInstance\(inst\)[\s\S]*?activeMonitorTab\.value = 'control'/);
assert.match(instanceHtml, /Instance model binding[\s\S]*?v-show="activeMonitorTab === 'control'"/);

const interactionHtml = fs.readFileSync(path.join(__dirname, 'interaction.html'), 'utf8');
assert.match(interactionHtml, /const newRouteDraftVisible=computed\(\(\)=>routeEditor\.dirty&&!routeEditor\.draft\.id\)/);
assert.match(interactionHtml, /新建路线（未保存）/);
assert.match(interactionHtml, /routeNameInput\.value\?\.focus\(\)/);
assert.doesNotMatch(interactionHtml, /routeEditor\.saving \|\| routeEditor\.defaultsDirty \|\| \(!routeEditor\.dirty/);
assert.doesNotMatch(interactionHtml, /routeEditor\.defaultsSaving \|\| !routeEditor\.defaultsDirty \|\| routeEditor\.dirty/);

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
    { rid: 'type.screen', name: '显示屏幕', category: '显示设备', source: 'ontotwin' },
    { rid: 'type.sofa', name: '模块沙发', category: '家具', source: 'ontotwin' },
    { rid: 'type.cad', name: '喷砂设备', category: '设备层', source: 'cad_auto:floor.dxf' },
    { rid: 'type.business-device', name: '业务设备', category: '设备层', source: 'graph_sync' },
    { rid: 'type.empty', name: '尚无实例类型' },
]);
assert.equal(typeGroups.find(group => group.fullLabel === '原 CAD 图层：设备层').items[0].rid, 'type.cad');
assert.equal(typeGroups.find(group => group.fullLabel === '业务分类：显示设备').items[0].rid, 'type.screen');
assert.equal(typeGroups.find(group => group.fullLabel === '业务分类：设备层').items[0].rid, 'type.business-device');
assert.equal(typeGroups.find(group => group.label === '业务分类：未分类').items[0].rid, 'type.empty');
assert.equal(typeGroups[0].originLabel, '原 CAD 图层');
assert.deepEqual(hierarchy.objectTypeCategoryPath({ category: '能源设备/动力' }), ['能源设备', '动力']);
assert.deepEqual(hierarchy.objectTypeGroupPath({ category: '设备层', source: 'cad_auto:floor.dxf' }), ['原 CAD 图层', '设备层']);
assert.equal(hierarchy.isCadGenerated({ source: 'cad_auto:floor.dxf' }), true);
assert.equal(hierarchy.isCadGenerated({ source: 'graph_sync' }), false);

const tiedPaths = hierarchy.dominantPathsByType([
    { object_type_rid: 'type.tie', hierarchy_path: ['航空展馆', 'LED屏幕', '主屏幕'] },
    { object_type_rid: 'type.tie', hierarchy_path: ['航空展馆', '显示与媒体设备'] },
]);
assert.deepEqual(tiedPaths.get('type.tie'), ['航空展馆', '显示与媒体设备']);

console.log('hierarchy_menu tests passed');
