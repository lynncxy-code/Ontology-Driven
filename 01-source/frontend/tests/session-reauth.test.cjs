const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');

const source = fs.readFileSync(path.join(__dirname, '../session_reauth.js'), 'utf8');

const json = (status, body) => ({ status, ok: status >= 200 && status < 300, body,
  clone() { return this; }, json: async () => body });

// The page is loaded inside an iframe whose top window owns the dialog, so
// the test can drive ensure() directly without a DOM.
function harness(responses, loginResult = true) {
  const calls = [];
  const top = { OntoTwinReauth: { ensure: async () => { top.asked++; return loginResult; } }, asked: 0 };
  const win = {
    fetch: async (input, init) => { calls.push({ input, init }); return responses.shift(); },
    sessionStorage: { getItem: () => '', setItem() {} },
  };
  win.top = top;
  const ctx = { window: win, location: { origin: 'http://127.0.0.1:5501' }, document: { addEventListener() {} },
    Request: class { constructor(url) { this.url = url; } clone() { return Object.assign(new this.constructor(this.url), { cloned: true }); } } };
  vm.createContext(ctx);
  vm.runInContext(source, ctx);
  return { win, top, calls, ctx };
}

test('expired session: re-login then the original request is resent and its result returned', async () => {
  const h = harness([json(401, { error: 'auth_required' }), json(200, { saved: true })]);
  const init = { method: 'DELETE', headers: { 'X-OntoTwin-Project-Id': 'p1' } };
  const r = await h.win.fetch('/api/v2/object-types/a/model-binding', init);
  assert.equal(r.status, 200);
  assert.deepEqual(await r.json(), { saved: true });
  assert.equal(h.top.asked, 1);
  assert.equal(h.calls.length, 2);
  assert.equal(h.calls[1].init, init, 'resend keeps the same body and headers');
});

test('session_expired is treated the same way', async () => {
  const h = harness([json(401, { error: 'session_expired' }), json(200, {})]);
  assert.equal((await h.win.fetch('/api/v4.8/organizations')).status, 200);
  assert.equal(h.top.asked, 1);
});

test('other 401s (wrong password, etc.) are passed through untouched', async () => {
  const h = harness([json(401, { error: 'invalid_credentials' })]);
  assert.equal((await h.win.fetch('/api/v4.8/auth/change-password', { method: 'POST' })).status, 401);
  assert.equal(h.top.asked, 0);
  assert.equal(h.calls.length, 1);
});

test('login request itself is never intercepted', async () => {
  const h = harness([json(401, { error: 'auth_required' })]);
  assert.equal((await h.win.fetch('/api/v4.8/auth/login', { method: 'POST' })).status, 401);
  assert.equal(h.top.asked, 0);
});

test('non-API and 403 responses are untouched', async () => {
  const h = harness([json(401, { error: 'auth_required' }), json(403, { error: 'forbidden' })]);
  assert.equal((await h.win.fetch('/release-info.json')).status, 401);
  assert.equal((await h.win.fetch('/api/v2/x')).status, 403);
  assert.equal(h.top.asked, 0);
});

test('user postpones re-login: original 401 goes back to the page, nothing resent', async () => {
  const h = harness([json(401, { error: 'auth_required' })], false);
  assert.equal((await h.win.fetch('/api/v2/x', { method: 'PUT' })).status, 401);
  assert.equal(h.calls.length, 1);
});

test('Request objects are resent from a copy taken before the first send', async () => {
  const h = harness([json(401, { error: 'auth_required' }), json(200, {})]);
  const req = new h.ctx.Request('/api/v2/y');
  assert.equal((await h.win.fetch(req)).status, 200);
  assert.equal(h.calls[1].input.cloned, true);
});

test('axios loaded after the script gets the same behaviour, retried only once', async () => {
  const h = harness([]);
  let handler = null; const sent = [];
  const ax = { interceptors: { response: { use: (_ok, bad) => { handler = bad; } } },
    request: async config => { sent.push(config); return { status: 200, data: { ok: 1 } }; } };
  h.win.axios = ax; // what the axios UMD bundle does when it loads
  assert.equal(h.win.axios, ax);
  assert.ok(handler, 'interceptor installed on assignment');
  const err = { config: { url: '/api/v2/instances/i/model-binding', method: 'put', data: '{"a":1}' }, response: { status: 401, data: { error: 'session_expired' } } };
  const r = await handler(err);
  assert.equal(r.status, 200);
  assert.equal(sent[0], err.config);
  assert.equal(h.top.asked, 1);
  await assert.rejects(handler(err), x => x === err, 'a request already resent once is not looped');
});

test('axios errors that are not an expired login are rethrown', async () => {
  const h = harness([]);
  let handler = null;
  h.win.axios = { interceptors: { response: { use: (_ok, bad) => { handler = bad; } } }, request: async () => assert.fail('no resend') };
  const err = { config: { url: '/api/v2/z' }, response: { status: 400, data: { error: 'project_id_required' } } };
  await assert.rejects(handler(err), x => x === err);
  await assert.rejects(handler({ config: { url: '/api/v2/z' } }), () => true, 'network errors pass through');
  assert.equal(h.top.asked, 0);
});
