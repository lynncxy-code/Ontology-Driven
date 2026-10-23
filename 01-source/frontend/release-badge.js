(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else api.mount(root.document, root.fetch.bind(root));
})(typeof window === 'undefined' ? globalThis : window, function () {
    'use strict';
    const environments = { business: ['业务环境', '业务'], test: ['测试环境', '测试'] };
    function formatUpdated(value, timeZone) {
        if (typeof value !== 'string' || !/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return '时间未标记';
        const date = new Date(value);
        if (!Number.isFinite(date.getTime())) return '时间未标记';
        try {
            return new Intl.DateTimeFormat('sv-SE', {
                timeZone: timeZone || 'UTC', year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', hour12: false, timeZoneName: 'shortOffset'
            }).format(date).replace('GMT', 'UTC');
        } catch (_) { return '时间未标记'; }
    }
    function normalize(data) {
        const text = (value, fallback) => typeof value === 'string' && value.trim() ? value.trim().slice(0, 240) : fallback;
        const key = data && data.environment;
        const env = Object.prototype.hasOwnProperty.call(environments, key) ? environments[key] : ['环境未标记', '未知'];
        return {
            environment: env[0], compact: env[1],
            version: text(data && data.version, '版本未标记'),
            updated: formatUpdated(data && data.updated_at, data && data.time_zone),
            backend: text(data && data.backend, '后端版本未标记'),
            note: text(data && data.note, '此处显示前端发布信息，不代表 UE 已加载相同版本的插件。')
        };
    }
    async function mount(document, fetcher) {
        const host = document.getElementById('release-badge');
        if (!host) return;
        host.innerHTML = `<button type="button" class="release-badge__trigger" aria-describedby="release-tooltip" aria-label="查看环境与版本"><span data-release="environment">读取版本中</span></button><section id="release-tooltip" class="release-badge__panel" role="tooltip" hidden><h2>环境与版本</h2><dl><dt>当前环境</dt><dd data-release="environment"></dd><dt>前端版本</dt><dd data-release="version"></dd><dt>前端更新时间</dt><dd data-release="updated"></dd><dt>后端版本</dt><dd data-release="backend"></dd></dl><p data-release="note" class="release-badge__note"></p></section>`;
        const trigger = host.querySelector('button');
        const panel = host.querySelector('[role="tooltip"]');
        const show = () => { panel.hidden = false; };
        const close = () => { panel.hidden = true; };
        host.addEventListener('mouseenter', show);
        host.addEventListener('mouseleave', close);
        trigger.addEventListener('focus', show);
        trigger.addEventListener('blur', close);
        trigger.addEventListener('click', show);
        document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
        document.addEventListener('click', event => { if (!host.contains(event.target)) close(); });
        document.defaultView.addEventListener('blur', close);
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        let data;
        try {
            const response = await fetcher('/release-info.json', { cache: 'no-store', signal: controller.signal });
            if (!response.ok) throw new Error('Release metadata unavailable');
            data = await response.json();
        } catch (_) { data = null; }
        finally { clearTimeout(timeout); }
        const release = normalize(data);
        host.querySelectorAll('[data-release]').forEach(element => { element.textContent = release[element.dataset.release]; });
        trigger.setAttribute('aria-label', `${release.environment}，查看版本详情`);
        host.dataset.loaded = 'true';
    }
    return { formatUpdated, normalize, mount };
});
