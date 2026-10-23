const assert = require('node:assert/strict');
const { test } = require('node:test');
const { normalize, formatUpdated } = require('../release-badge.js');
test('deployment metadata distinguishes business and test; never infers environment from port', () => {
    assert.equal(normalize({environment:'business'}).environment, '业务环境');
    assert.equal(normalize({environment:'test'}).environment, '测试环境');
    assert.equal(normalize({environment:'production'}).environment, '环境未标记');
    assert.equal(normalize({environment:'__proto__'}).environment, '环境未标记');
    assert.equal(normalize(null).version, '版本未标记');
});
test('timestamp is fixed deployment time with explicit timezone, not current file/browser time', () => {
    assert.equal(formatUpdated('2026-10-23T05:51:51Z', 'Asia/Seoul'), '2026-10-23 14:51 UTC+9');
    assert.equal(formatUpdated('2026-10-23T05:51:51Z', 'Asia/Shanghai'), '2026-10-23 13:51 UTC+8');
    for (const value of [null, '', 'not-a-date', '2026-10-23 14:51:00']) assert.equal(formatUpdated(value), '时间未标记');
    assert.equal(formatUpdated('2026-10-23T05:51:51Z', 'invalid/zone'), '时间未标记');
});
test('missing versions stay unknown and labels remain bounded plain strings', () => {
    assert.equal(normalize({}).backend, '后端版本未标记');
    assert.equal(normalize({version:'x'.repeat(500)}).version.length, 240);
    assert.equal(normalize({version:123}).version, '版本未标记');
});
