// OntoTwin 版本显示（NEW-13）：全产品一个版本号，账号菜单和 Nexus 角标共用这一份。
// 只显示版本号、更新时间，以及当前项目绑定的 UE 关卡插件是否同一版；不显示内部编号。
(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else {
        root.OntoTwinRelease = api;
        api.mount(root.document, root.fetch.bind(root));
    }
})(typeof window === 'undefined' ? globalThis : window, function () {
    'use strict';
    const text = (value, fallback, max) => typeof value === 'string' && value.trim() ? value.trim().slice(0, max || 120) : fallback;

    // 按看的人自己电脑的时区显示，并标出时区，例如 2026-11-24 10:39 UTC+8
    function formatUpdated(value, timeZone) {
        if (typeof value !== 'string' || !/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return '';
        const date = new Date(value);
        if (!Number.isFinite(date.getTime())) return '';
        try {
            return new Intl.DateTimeFormat('sv-SE', {
                timeZone: timeZone || undefined, year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', hour12: false, timeZoneName: 'shortOffset'
            }).format(date).replace('GMT', 'UTC');
        } catch (_) { return ''; }
    }

    function normalize(data) {
        const version = text(data && data.version, '');
        const updated = formatUpdated(data && data.updated_at);
        return {
            display: text(data && data.display, version ? 'OntoTwin ' + version : '版本信息暂不可用'),
            label: text(data && data.label, version || '版本未知', 40),
            updated: updated ? '更新于 ' + updated : '更新时间未记录'
        };
    }

    const STATUS = {
        same: ['ok', () => '同一版'],
        different: ['warn', (row, backend) => '不是同一版：插件是' + (row.plugin_label || '其他版本') + '，后台是' + backend + '。请装上' + backend + ' 的插件。'],
        unknown: ['muted', (row, backend) => '版本未知：这个 UE 工程的插件太旧，不会报告版本。装上' + backend + ' 的插件后才能比对。']
    };

    // 只看当前项目绑定的 UE 关卡；没有进项目（或未登录）时整块不显示
    function pluginRows(data) {
        if (!data || !Array.isArray(data.items) || !data.project_id) return null;
        const backend = text(data.backend_label, '当前版本', 40);
        const rows = data.items.slice(0, 50).map(row => {
            const status = STATUS[row && row.status] || STATUS.unknown;
            return {
                name: text(row && row.ue_project_name, 'UE 工程') + ' · ' + text(row && row.scene_name, '未命名关卡'),
                tone: status[0],
                status: status[1](row || {}, backend)
            };
        });
        const empty = rows.length ? '' : (data.bound ? '这个项目绑定的 UE 关卡最近 7 天没有连过后台' : '这个项目还没有绑定 UE 关卡');
        return { rows, empty };
    }

    async function getJson(fetcher, url) {
        const controller = typeof AbortController === 'function' ? new AbortController() : null;
        const timer = controller ? setTimeout(() => controller.abort(), 5000) : null;
        try {
            const response = await fetcher(url, { cache: 'no-store', credentials: 'same-origin', signal: controller && controller.signal });
            return response.ok ? await response.json() : null;
        } catch (_) { return null; }
        finally { if (timer) clearTimeout(timer); }
    }

    async function load(fetcher) {
        const [info, plugins] = await Promise.all([getJson(fetcher, '/release-info.json'), getJson(fetcher, '/api/v4.8/release/ue-plugins')]);
        return { release: normalize(info), plugins: pluginRows(plugins) };
    }

    function el(document, tag, className, content) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (content != null) node.textContent = content;
        return node;
    }

    function render(document, container, state) {
        container.textContent = '';
        container.appendChild(el(document, 'div', 'ot-release__name', state.release.display));
        container.appendChild(el(document, 'div', 'ot-release__time', state.release.updated));
        if (!state.plugins) return;
        const block = el(document, 'div', 'ot-release__plugins');
        block.appendChild(el(document, 'div', 'ot-release__heading', '本项目的 UE 关卡'));
        if (state.plugins.empty) block.appendChild(el(document, 'div', 'ot-release__empty', state.plugins.empty));
        state.plugins.rows.forEach(row => {
            const item = el(document, 'div', 'ot-release__row');
            item.appendChild(el(document, 'div', 'ot-release__project', row.name));
            const status = el(document, 'div', 'ot-release__status');
            status.appendChild(el(document, 'span', 'ot-release__dot ot-release__dot--' + row.tone));
            status.appendChild(el(document, 'span', '', row.status));
            item.appendChild(status);
            block.appendChild(item);
        });
        container.appendChild(block);
    }

    // Nexus 顶栏角标：显示“候选 25”，悬停或点击看详情
    async function mount(document, fetcher) {
        const host = document && document.getElementById('release-badge');
        if (!host) return;
        host.innerHTML = '<button type="button" class="release-badge__trigger" aria-describedby="release-tooltip" aria-label="查看版本">读取版本中</button><section id="release-tooltip" class="release-badge__panel ot-release" role="tooltip" hidden></section>';
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
        const state = await load(fetcher);
        trigger.textContent = state.release.label;
        trigger.setAttribute('aria-label', state.release.display + '，查看版本详情');
        render(document, panel, state);
        host.dataset.loaded = 'true';
    }

    return { formatUpdated, normalize, pluginRows, load, render, mount };
});
