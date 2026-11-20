(function () {
  // OPT-04：登录过期后原地重新登录。
  //
  // 页面打开太久（超过登录有效期）后，后台对业务请求返回 401
  // auth_required / session_expired。以前页面只显示一行红字，用户以为
  // 自己还登录着，反复点击都失败。这里在请求层统一拦住这两种 401：
  // 原地弹出登录框，登录成功后把被拒的那次请求原样重发，并把结果交还
  // 给原来的调用方。整个过程页面不刷新，所以表单里未保存的内容都还在。
  //
  // 本脚本必须先于 account_context.js 加载：上下文桥包在本包装的外层，
  // 重发的请求因此仍带着原来的组织 / 工厂 / 项目请求头。
  if (window.OntoTwinReauth) return;

  const EXPIRED_CODES = ['auth_required', 'session_expired'];
  const LOGIN_URL = '/api/v4.8/auth/login';
  const nativeFetch = window.fetch ? window.fetch.bind(window) : null;
  let pending = null;   // 正在进行的重新登录（所有被拒请求共用一个）
  let dismissed = false; // 用户点了“稍后”：不再自动弹框，只显示提示条

  const isApi = url => /^(?:https?:\/\/[^/]+)?\/api\//.test(url) || url.indexOf(location.origin + '/api/') === 0;
  const isLogin = url => url.indexOf(LOGIN_URL) >= 0;
  const shouldIntercept = url => isApi(url) && !isLogin(url) && url.indexOf('/api/v4.8/auth/logout') < 0;
  const isExpired = (status, body) => status === 401 && !!body && EXPIRED_CODES.indexOf(body.error) >= 0;

  function stores() {
    const list = [];
    try { list.push(window.sessionStorage); } catch (_) {}
    try { if (window.top !== window) list.push(window.top.sessionStorage); } catch (_) {}
    return list.filter(Boolean);
  }
  function read(key) {
    for (const s of stores()) { try { const v = s.getItem(key); if (v) return v; } catch (_) {} }
    return '';
  }

  // 嵌在工作台外壳 iframe 里的页面，把登录框交给最外层页面统一弹出，
  // 避免外壳和多个内页同时各弹一个。
  function topGuard() {
    try {
      if (window.top !== window && window.top.OntoTwinReauth && window.top.OntoTwinReauth !== api) return window.top.OntoTwinReauth;
    } catch (_) {}
    return null;
  }

  function ensure() {
    const outer = topGuard();
    if (outer) return outer.ensure();
    if (pending) return pending;
    if (dismissed) { showBanner(); return Promise.resolve(false); }
    pending = openDialog().then(ok => { pending = null; return ok; });
    return pending;
  }

  async function restoreContext() {
    const org = read('ontotwin_organization_id');
    if (!org || !nativeFetch) return;
    const body = { organization_id: org, factory_id: read('ontotwin_factory_id') || null, project_id: read('ontotwin_project_id') || null };
    try {
      await nativeFetch('/api/v4.8/context', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    } catch (_) { /* 请求头里仍带着本页上下文，恢复失败不影响重发 */ }
  }

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  const STYLE = '.ot-reauth-mask{position:fixed;inset:0;background:rgba(20,20,20,.4);display:flex;align-items:center;justify-content:center;z-index:2147483000;font-family:Inter,"Microsoft YaHei",sans-serif}' +
    '.ot-reauth{background:#fff;border-radius:12px;box-shadow:0 16px 48px rgba(20,20,20,.18);width:min(380px,92vw);padding:24px;color:#1a1a1a;box-sizing:border-box}' +
    '.ot-reauth h3{margin:0 0 8px;font-size:16px;font-weight:600}.ot-reauth p{margin:0 0 16px;font-size:13px;line-height:1.6;color:#5c5c5c}' +
    '.ot-reauth label{display:block;font-size:12px;color:#5c5c5c;margin:0 0 4px}.ot-reauth input{display:block;width:100%;box-sizing:border-box;padding:8px 10px;margin:0 0 12px;border:1px solid #d4d4d4;border-radius:6px;font-size:13px;background:#fff;color:#1a1a1a}' +
    '.ot-reauth input:focus{outline:none;border-color:#1a1a1a;box-shadow:0 0 0 3px rgba(26,26,26,.06)}.ot-reauth input[readonly]{background:#fafafa;color:#5c5c5c}' +
    '.ot-reauth-error{min-height:18px;font-size:12px;color:#b42318;margin:0 0 8px}.ot-reauth-actions{display:flex;justify-content:flex-end;gap:8px}' +
    '.ot-reauth button{font:500 13px/1 inherit;padding:8px 14px;border-radius:8px;border:1px solid #d4d4d4;background:#fff;color:#1a1a1a;cursor:pointer}' +
    '.ot-reauth button:hover{background:#f3f3f3}.ot-reauth .ot-reauth-primary{background:#1a1a1a;color:#fff;border-color:#1a1a1a}.ot-reauth .ot-reauth-primary:hover{background:#000}.ot-reauth button:disabled{opacity:.4;cursor:not-allowed}' +
    '.ot-reauth-switch{font-size:12px;color:#8a8a8a;margin:12px 0 0}.ot-reauth-switch a{color:#5c5c5c}' +
    '.ot-reauth-banner{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:2147483000;background:#fff;border:1px solid #e8e8e8;border-left:2px solid #b54708;border-radius:8px;box-shadow:0 4px 16px rgba(20,20,20,.08);padding:10px 14px;font:13px Inter,"Microsoft YaHei",sans-serif;color:#1a1a1a;display:flex;gap:12px;align-items:center}' +
    '.ot-reauth-banner button{font:500 12px/1 inherit;padding:6px 10px;border-radius:6px;border:1px solid #1a1a1a;background:#1a1a1a;color:#fff;cursor:pointer}';

  function installStyle() {
    if (document.getElementById('ot-reauth-style')) return;
    const s = document.createElement('style');
    s.id = 'ot-reauth-style';
    s.textContent = STYLE;
    (document.head || document.documentElement).appendChild(s);
  }

  let banner = null;
  function showBanner() {
    if (banner || !document.body) return;
    installStyle();
    banner = document.createElement('div');
    banner.className = 'ot-reauth-banner';
    banner.setAttribute('role', 'status');
    banner.innerHTML = '<span>登录已过期，当前操作无法保存。页面上的内容仍然保留。</span><button type="button">重新登录</button>';
    banner.querySelector('button').onclick = () => { dismissed = false; hideBanner(); ensure(); };
    document.body.appendChild(banner);
  }
  function hideBanner() { if (banner) { banner.remove(); banner = null; } }

  function openDialog() {
    return new Promise(resolve => {
      const start = () => {
        installStyle();
        hideBanner();
        const known = read('ontotwin_login_name');
        const mask = document.createElement('div');
        mask.className = 'ot-reauth-mask';
        mask.innerHTML = '<form class="ot-reauth" role="dialog" aria-modal="true" aria-labelledby="otReauthTitle" autocomplete="on">' +
          '<h3 id="otReauthTitle">登录已过期</h3>' +
          '<p>为了安全，登录超过有效期后需要重新输入密码。重新登录后，刚才的操作会自动继续；页面上未保存的内容不会丢失。</p>' +
          '<label for="otReauthName">账号</label><input id="otReauthName" name="username" autocomplete="username" value="' + esc(known) + '"' + (known ? ' readonly' : '') + '>' +
          '<label for="otReauthPassword">密码</label><input id="otReauthPassword" name="password" type="password" autocomplete="current-password">' +
          '<div class="ot-reauth-error" aria-live="polite"></div>' +
          '<div class="ot-reauth-actions"><button type="button" data-act="later">稍后</button><button type="submit" class="ot-reauth-primary">重新登录</button></div>' +
          (known ? '<p class="ot-reauth-switch">要换一个账号，请先保存好手头内容，再<a href="/account" target="_top">到登录页</a>登录。</p>' : '') +
          '</form>';
        document.body.appendChild(mask);
        const form = mask.querySelector('form');
        const nameEl = mask.querySelector('#otReauthName');
        const pwdEl = mask.querySelector('#otReauthPassword');
        const errEl = mask.querySelector('.ot-reauth-error');
        const submit = mask.querySelector('.ot-reauth-primary');
        const close = ok => { mask.remove(); resolve(ok); };
        (known ? pwdEl : nameEl).focus();
        mask.querySelector('[data-act="later"]').onclick = () => { dismissed = true; close(false); showBanner(); };
        form.onsubmit = async e => {
          e.preventDefault();
          const login_name = nameEl.value.trim();
          if (!login_name || !pwdEl.value) { errEl.textContent = '请输入账号和密码'; return; }
          submit.disabled = true; errEl.textContent = '';
          try {
            const r = await nativeFetch(LOGIN_URL, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ login_name, password: pwdEl.value }) });
            const d = await r.json().catch(() => ({}));
            if (!r.ok) throw new Error(d.message || '登录失败');
            if (d.must_change_password) throw new Error('该账号需要先修改密码，请保存好手头内容后到登录页处理');
            for (const s of stores()) { try { s.setItem('ontotwin_login_name', login_name); } catch (_) {} }
            await restoreContext();
            close(true);
          } catch (err) {
            errEl.textContent = err.message || '登录失败';
            pwdEl.value = '';
            pwdEl.focus();
          } finally { submit.disabled = false; }
        };
      };
      if (document.body) start(); else document.addEventListener('DOMContentLoaded', start, { once: true });
    });
  }

  async function expiredBody(response) {
    if (!response || response.status !== 401) return false;
    try { return isExpired(response.status, await response.clone().json()); } catch (_) { return false; }
  }

  // ── fetch ──────────────────────────────────────────────────────
  if (nativeFetch) {
    window.fetch = async function (input, init) {
      const url = typeof input === 'string' ? input : (input && input.url) || String(input || '');
      if (!shouldIntercept(url)) return nativeFetch(input, init);
      // Request 对象的请求体只能读一次，先留一份副本用于重发。
      const spare = (typeof Request !== 'undefined' && input instanceof Request) ? input.clone() : input;
      const response = await nativeFetch(input, init);
      if (!(await expiredBody(response))) return response;
      if (!(await ensure())) return response;
      return nativeFetch(spare, init);
    };
  }

  // ── axios（旧业务页用 axios 发请求）────────────────────────────
  function patchAxios(ax) {
    if (!ax || !ax.interceptors || ax.__otReauth) return ax;
    ax.__otReauth = true;
    ax.interceptors.response.use(null, async error => {
      const res = error && error.response;
      const config = error && error.config;
      if (!res || !config || config.__otReauthRetried || !shouldIntercept(String(config.url || ''))) throw error;
      if (!isExpired(res.status, res.data)) throw error;
      if (!(await ensure())) throw error;
      config.__otReauthRetried = true;
      return ax.request(config);
    });
    return ax;
  }
  let axiosRef = window.axios;
  patchAxios(axiosRef);
  try {
    Object.defineProperty(window, 'axios', {
      configurable: true,
      enumerable: true,
      get() { return axiosRef; },
      set(v) { axiosRef = patchAxios(v); },
    });
  } catch (_) {
    document.addEventListener('DOMContentLoaded', () => patchAxios(window.axios));
  }

  const api = { ensure, isExpired, shouldIntercept, patchAxios };
  window.OntoTwinReauth = api;
})();
