(function () {
  if (location.pathname === '/account') return;

  const inFrame = window.self !== window.top;
  const nativeFetch = window.fetch.bind(window);
  const storage = () => {
    try { return window.sessionStorage; } catch (_) { return null; }
  };
  const context = () => {
    const keys = ['ontotwin_organization_id', 'ontotwin_factory_id', 'ontotwin_project_id'];
    const read = (store) => store ? keys.map(k => store.getItem(k) || '') : ['', '', ''];
    let values = read(storage());
    if (inFrame && (!values[0] || !values[1] || !values[2])) {
      try { values = read(window.parent.sessionStorage).map((v, i) => v || values[i]); } catch (_) {}
    }
    return { organization_id: values[0], factory_id: values[1], project_id: values[2] };
  };
  const remember = (key, value) => {
    if (!value) return;
    try { storage()?.setItem(key, value); } catch (_) {}
    if (inFrame) {
      try { window.parent.sessionStorage.setItem(key, value); } catch (_) {}
    }
  };

  // This script is injected synchronously so legacy inline body scripts cannot
  // issue their first request before the project bridge is installed.
  window.fetch = function (input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const match = url.match(/\/api\/v2\/ontology\/datasets\/([^/?#]+)/);
    const current = context();
    let pid = (match ? decodeURIComponent(match[1]) : '') || current.project_id || '';
    if (url.indexOf('/api/v2/ontology/datasets/activate') >= 0 && init && init.body) {
      try {
        const parsed = typeof init.body === 'string' ? JSON.parse(init.body) : null;
        if (parsed && parsed.dataset_id) pid = parsed.dataset_id;
      } catch (_) { /* multipart/legacy body */ }
    }
    if (url.indexOf('/api/v2/') >= 0 || url.indexOf('/api/v4.8/') >= 0) {
      init = init ? Object.assign({}, init) : {};
      const headers = new Headers(init.headers || ((input && input.headers) || {}));
      if (current.organization_id && !headers.has('X-OntoTwin-Organization-Id')) headers.set('X-OntoTwin-Organization-Id', current.organization_id);
      if (current.factory_id && !headers.has('X-OntoTwin-Factory-Id')) headers.set('X-OntoTwin-Factory-Id', current.factory_id);
      if (pid && !headers.has('X-OntoTwin-Project-Id')) headers.set('X-OntoTwin-Project-Id', pid);
      init.headers = headers;
    }
    return nativeFetch(input, init).then(response => {
      if (url.indexOf('/api/v2/ontology/datasets') >= 0 && response.ok) {
        response.clone().json().then(items => {
          const list = Array.isArray(items) ? items : (items && items.items) || [];
          const active = list.find(x => x && x.is_active && x.project_id);
          if (active) remember('ontotwin_project_id', active.project_id);
        }).catch(() => {});
      }
      return response;
    });
  };

  // Some legacy business pages use Axios, whose browser adapter talks to
  // XMLHttpRequest instead of fetch.  Install the same request-scoped
  // headers at the transport boundary so iframe pages cannot silently lose
  // their project context just because a page uses Axios.
  const xhrProto = window.XMLHttpRequest && window.XMLHttpRequest.prototype;
  if (xhrProto && !xhrProto.__ot48ContextBridge) {
    const nativeOpen = xhrProto.open;
    const nativeSetRequestHeader = xhrProto.setRequestHeader;
    const nativeSend = xhrProto.send;
    xhrProto.open = function (method, url) {
      this.__ot48Url = String(url || '');
      return nativeOpen.apply(this, arguments);
    };
    xhrProto.setRequestHeader = function (name, value) {
      return nativeSetRequestHeader.call(this, name, value);
    };
    xhrProto.send = function (body) {
      const url = this.__ot48Url || '';
      if (url.indexOf('/api/v2/') >= 0 || url.indexOf('/api/v4.8/') >= 0) {
        const current = context();
        const match = url.match(/\/api\/v2\/ontology\/datasets\/([^/?#]+)/);
        const pid = (match ? decodeURIComponent(match[1]) : '') || current.project_id || '';
        try {
          if (current.organization_id) this.setRequestHeader('X-OntoTwin-Organization-Id', current.organization_id);
          if (current.factory_id) this.setRequestHeader('X-OntoTwin-Factory-Id', current.factory_id);
          if (pid) this.setRequestHeader('X-OntoTwin-Project-Id', pid);
        } catch (_) { /* a caller may have already sent this XHR */ }
      }
      return nativeSend.call(this, body);
    };
    xhrProto.__ot48ContextBridge = true;
  }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // The iframe needs the fetch bridge but must not render a second account
  // menu on top of the Nexus shell.
  if (inFrame) return;

  const tabContext = context();
  fetch('/api/v4.8/auth/me', { credentials: 'same-origin' }).then(r => r.ok ? r.json() : null).then(me => {
    if (!me || !me.user) return;
    // Never bootstrap a new tab from the server's shared legacy context row.
    // Only refresh a context that this tab has already explicitly selected.
    if (me.context && (tabContext.organization_id || tabContext.factory_id || tabContext.project_id)) {
      remember('ontotwin_organization_id', me.context.organization_id);
      remember('ontotwin_factory_id', me.context.factory_id);
      remember('ontotwin_project_id', me.context.project_id);
    }
    const wrap = document.createElement('div');
    wrap.className = 'ot48-account-menu';
    const initials = (me.user.display_name || me.user.login_name || 'U').slice(0, 1).toUpperCase();
    const currentOrg = (me.organizations || []).find(o => o.organization_id === (me.context && me.context.organization_id));
    wrap.innerHTML = '<button class="ot48-account-trigger" aria-label="账号菜单">' + initials + '</button>' +
      '<div class="ot48-account-panel"><div class="ot48-account-identity"><strong>' + esc(me.user.display_name || me.user.login_name) + '</strong><span id="ot48ContextLabel">' + esc(currentOrg?.name || '未选择组织') + '</span></div>' +
      '<button class="ot48-account-item" data-action="switch">切换组织／工厂</button><button class="ot48-account-item" data-action="personal">个人设置</button><button class="ot48-account-item" data-action="settings">组织管理</button><button class="ot48-account-item" data-action="version">环境与版本信息</button><button class="ot48-account-item" data-action="logout">退出登录</button><div class="ot48-account-version" id="ot48Version"></div></div>';
    document.body.appendChild(wrap);
    const trigger = wrap.querySelector('.ot48-account-trigger');
    trigger.onclick = () => wrap.classList.toggle('open');
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) wrap.classList.remove('open'); });
    wrap.querySelector('[data-action="switch"]').onclick = () => location.href = '/account?mode=switch';
    wrap.querySelector('[data-action="settings"]').onclick = () => location.href = '/organization?mode=manage';
    wrap.querySelector('[data-action="personal"]').onclick = () => location.href = '/account?mode=personal';
    wrap.querySelector('[data-action="logout"]').onclick = async () => {
      await fetch('/api/v4.8/auth/logout', { method: 'POST', credentials: 'same-origin' });
      try { sessionStorage.clear(); } catch (_) {}
      location.href = '/account';
    };
    wrap.querySelector('[data-action="version"]').onclick = async () => {
      const e = wrap.querySelector('#ot48Version');
      if (e.dataset.loaded === 'true') { e.hidden = !e.hidden; return; }
      try {
        const d = await fetch('/release-info.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : null);
        if (!d) throw new Error('release metadata unavailable');
        const env = d.environment === 'business' ? '业务环境' : (d.environment === 'test' ? '测试环境' : '环境未标记');
        let updated = '时间未标记';
        if (d.updated_at) {
          const date = new Date(d.updated_at);
          if (Number.isFinite(date.getTime())) updated = new Intl.DateTimeFormat('sv-SE', { timeZone: d.time_zone || 'UTC', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false, timeZoneName: 'shortOffset' }).format(date).replace('GMT', 'UTC');
        }
        e.innerHTML = '<div class="ot48-version-row"><span>当前环境</span><strong>' + esc(env) + '</strong></div>' +
          '<div class="ot48-version-row"><span>前端版本</span><strong>' + esc(d.version || '版本未标记') + '</strong></div>' +
          '<div class="ot48-version-row"><span>前端更新时间</span><strong>' + esc(updated) + '</strong></div>' +
          '<div class="ot48-version-row"><span>后端版本</span><strong>' + esc(d.backend || '后端版本未标记') + '</strong></div>' +
          '<div class="ot48-version-note">' + esc(d.note || '此处显示前端发布信息，不代表 UE 已加载相同版本的插件。') + '</div>';
        e.hidden = false; e.dataset.loaded = 'true';
      } catch (_) { e.textContent = '版本信息暂不可用'; e.hidden = false; }
    };
  }).catch(() => {});
})();
