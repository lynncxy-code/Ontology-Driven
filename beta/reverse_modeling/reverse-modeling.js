(function () {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const VIEW_KEYS = ['front', 'back', 'left', 'right'];
  const VIEW_NAMES = { front: '正面', back: '后面', left: '左侧', right: '右侧' };

  const elements = {
    sidebar: $('#sidebar'),
    sidebarToggle: $('#sidebarToggle'),
    servicePill: $('#servicePill'),
    serviceDot: $('#serviceDot'),
    serviceText: $('#serviceText'),
    clearAllViews: $('#clearAllViews'),
    viewCount: $('#viewCount'),
    removeBackground: $('#removeBackground'),
    randomSeed: $('#randomSeed'),
    seedInput: $('#seedInput'),
    stepsInput: $('#stepsInput'),
    stepsValue: $('#stepsValue'),
    octreeInput: $('#octreeInput'),
    octreeValue: $('#octreeValue'),
    guidanceInput: $('#guidanceInput'),
    chunksInput: $('#chunksInput'),
    generateButton: $('#generateButton'),
    generateButtonText: $('#generateButtonText'),
    generateNote: $('#generateNote'),
    emptyState: $('#emptyState'),
    generatedViewer: $('#generatedViewer'),
    exportViewer: $('#exportViewer'),
    statsView: $('#statsView'),
    statsGrid: $('#statsGrid'),
    statsRaw: $('#statsRaw'),
    jobOverlay: $('#jobOverlay'),
    jobTitle: $('#jobTitle'),
    jobDetail: $('#jobDetail'),
    previewDot: $('#previewDot'),
    previewStateText: $('#previewStateText'),
    jobDot: $('#jobDot'),
    jobStatus: $('#jobStatus'),
    jobStatusDetail: $('#jobStatusDetail'),
    resultMode: $('#resultMode'),
    resultViews: $('#resultViews'),
    resultSeed: $('#resultSeed'),
    resultFiles: $('#resultFiles'),
    recoverButton: $('#recoverButton'),
    generatedDownloads: $('#generatedDownloads'),
    fileType: $('#fileType'),
    simplifyMesh: $('#simplifyMesh'),
    targetFacesRow: $('#targetFacesRow'),
    targetFaces: $('#targetFaces'),
    textureExportRow: $('#textureExportRow'),
    textureExportHelp: $('#textureExportHelp'),
    includeTexture: $('#includeTexture'),
    exportButton: $('#exportButton'),
    downloadButton: $('#downloadButton'),
    exampleGrid: $('#exampleGrid'),
    refreshExamples: $('#refreshExamples'),
    toastRegion: $('#toastRegion')
  };

  const viewElements = Object.fromEntries(VIEW_KEYS.map((view) => [view, {
    card: $('[data-view-card="' + view + '"]'),
    upload: $('[data-view-upload="' + view + '"]'),
    input: $('[data-view-input="' + view + '"]'),
    empty: $('[data-view-empty="' + view + '"]'),
    preview: $('[data-view-preview="' + view + '"]'),
    clear: $('[data-clear-view="' + view + '"]')
  }]));

  const state = {
    files: { front: null, back: null, left: null, right: null },
    fileObjectUrls: { front: null, back: null, left: null, right: null },
    serviceMode: null,
    mode: 'shape',
    serviceOnline: false,
    generating: false,
    exporting: false,
    recovering: false,
    generationJobId: null,
    generationResult: null,
    exportResult: null,
    activeView: 'generated'
  };

  function toast(message, type = 'info') {
    const item = document.createElement('div');
    item.className = 'toast-item' + (type === 'ok' ? ' ok' : type === 'err' ? ' err' : '');
    item.textContent = message;
    elements.toastRegion.appendChild(item);
    window.setTimeout(() => {
      item.style.opacity = '0';
      window.setTimeout(() => item.remove(), 180);
    }, 2800);
  }

  function setDot(element, tone) {
    element.className = 'dot dot-' + tone;
  }

  function setBusyOverlay(show, title, detail) {
    elements.jobOverlay.hidden = !show;
    if (title) elements.jobTitle.textContent = title;
    if (detail) elements.jobDetail.textContent = detail;
  }

  function updateGenerateAvailability() {
    const viewCount = VIEW_KEYS.filter((view) => Boolean(state.files[view])).length;
    const hasFront = Boolean(state.files.front);
    const canGenerate = Boolean(hasFront && state.serviceOnline && !state.generating && !state.exporting && !state.recovering);
    elements.generateButton.disabled = !canGenerate;
    elements.clearAllViews.disabled = viewCount === 0;
    elements.recoverButton.disabled = state.generating || state.exporting || state.recovering;
    elements.viewCount.textContent = viewCount + ' / 4 已添加';
    if (!state.generationResult) elements.resultViews.textContent = viewCount ? viewCount + ' 个方向' : '—';
    elements.generateButtonText.textContent = state.generating
      ? '正在生成'
      : state.mode === 'textured'
        ? '生成形体与材质'
        : '生成形体草稿';
    if (!state.serviceOnline) {
      elements.generateNote.textContent = location.protocol === 'file:'
        ? '请通过启动脚本打开本页面，才能调用本地模型。'
        : state.serviceMode === 'single'
          ? '当前是单图服务，请改用 Hunyuan3D-2mv 启动脚本。'
          : '请先启动本地 Hunyuan3D-2mv 服务。';
    } else if (!hasFront) {
      elements.generateNote.textContent = '至少添加正面视图后即可开始。';
    } else if (state.generating) {
      elements.generateNote.textContent = '生成期间请保持多视图服务窗口开启。';
    } else if (viewCount === 1) {
      elements.generateNote.textContent = '可以生成；继续补充后、左、右视图可减少结构猜测。';
    } else {
      elements.generateNote.textContent = state.mode === 'textured'
        ? '将使用 ' + viewCount + ' 个视图依次生成形体与 PBR 材质。'
        : '将使用 ' + viewCount + ' 个视图生成形体草稿。';
    }
  }

  function setServiceState(payload) {
    state.serviceOnline = Boolean(payload && payload.online);
    state.serviceMode = payload && payload.mode ? payload.mode : null;
    setDot(elements.serviceDot, state.serviceOnline ? 'ok' : 'err');
    const serviceLabel = state.serviceOnline
      ? '多视图生成服务已连接'
      : state.serviceMode === 'single'
        ? '当前连接的是单图服务'
        : '多视图生成服务未连接';
    elements.serviceText.textContent = serviceLabel;
    elements.servicePill.setAttribute('aria-label', serviceLabel + '，点击重新检查');
    updateGenerateAvailability();
  }

  async function checkService(showFeedback = false) {
    setDot(elements.serviceDot, 'muted');
    elements.serviceText.textContent = '正在检查本地服务';
    try {
      const response = await fetch('/api/health', { cache: 'no-store' });
      if (!response.ok) throw new Error('服务检查失败');
      const payload = await response.json();
      setServiceState(payload);
      if (showFeedback) toast(payload.message || (payload.online ? '服务已连接' : '服务未连接'), payload.online ? 'ok' : 'err');
    } catch (error) {
      setServiceState({ online: false });
      if (showFeedback) toast('无法连接 Beta 页面服务，请使用启动脚本打开。', 'err');
    }
  }

  function setViewFile(view, file) {
    if (!VIEW_KEYS.includes(view)) return;
    if (!file) return;
    const allowed = ['image/png', 'image/jpeg', 'image/webp'];
    if (!allowed.includes(file.type)) {
      toast('仅支持 PNG、JPG 或 WebP 图片。', 'err');
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      toast('图片不能超过 25 MB。', 'err');
      return;
    }
    if (state.fileObjectUrls[view]) URL.revokeObjectURL(state.fileObjectUrls[view]);
    state.files[view] = file;
    state.fileObjectUrls[view] = URL.createObjectURL(file);
    viewElements[view].preview.src = state.fileObjectUrls[view];
    viewElements[view].preview.hidden = false;
    viewElements[view].empty.hidden = true;
    viewElements[view].clear.hidden = false;
    viewElements[view].card.classList.add('has-file');
    viewElements[view].upload.setAttribute('aria-label', VIEW_NAMES[view] + '视图已添加：' + file.name + '，点击替换');
    updateGenerateAvailability();
  }

  function clearView(view) {
    if (!VIEW_KEYS.includes(view)) return;
    if (state.fileObjectUrls[view]) URL.revokeObjectURL(state.fileObjectUrls[view]);
    state.files[view] = null;
    state.fileObjectUrls[view] = null;
    viewElements[view].input.value = '';
    viewElements[view].preview.removeAttribute('src');
    viewElements[view].preview.hidden = true;
    viewElements[view].empty.hidden = false;
    viewElements[view].clear.hidden = true;
    viewElements[view].card.classList.remove('has-file');
    viewElements[view].upload.setAttribute('aria-label', '选择或拖入' + VIEW_NAMES[view] + '视图');
    updateGenerateAvailability();
  }

  function clearAllViews() {
    VIEW_KEYS.forEach(clearView);
  }

  function setMode(mode) {
    state.mode = mode === 'textured' ? 'textured' : 'shape';
    $$('.segment').forEach((button) => {
      const active = button.dataset.mode === state.mode;
      button.classList.toggle('active', active);
      button.setAttribute('aria-checked', String(active));
    });
    elements.resultMode.textContent = state.mode === 'textured' ? '形体与材质' : '形体草稿';
    updateGenerateAvailability();
  }

  function setJobStatus(status, detail, tone) {
    elements.jobStatus.textContent = status;
    elements.jobStatusDetail.textContent = detail;
    setDot(elements.jobDot, tone);
    elements.previewStateText.textContent = status;
    setDot(elements.previewDot, tone);
  }

  function activateView(view) {
    if (view === 'export' && !state.exportResult) return;
    state.activeView = view;
    $$('.view-tab').forEach((button) => {
      const active = button.dataset.view === view;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', String(active));
    });
    const hasGenerated = Boolean(state.generationResult);
    elements.emptyState.hidden = hasGenerated || view === 'stats';
    elements.generatedViewer.hidden = !(view === 'generated' && hasGenerated);
    elements.exportViewer.hidden = !(view === 'export' && state.exportResult);
    elements.statsView.hidden = view !== 'stats';
  }

  function flattenStats(value, prefix = '', rows = []) {
    if (value == null) return rows;
    if (typeof value === 'object' && !Array.isArray(value)) {
      Object.entries(value).forEach(([key, item]) => flattenStats(item, prefix ? prefix + ' · ' + key : key, rows));
    } else if (Array.isArray(value)) {
      if (value.length <= 4 && value.every((item) => ['string', 'number', 'boolean'].includes(typeof item))) rows.push([prefix, value.join(', ')]);
    } else {
      rows.push([prefix || '值', value]);
    }
    return rows;
  }

  function friendlyStatName(name) {
    const lower = String(name).toLowerCase();
    const aliases = [
      ['number of vertices', '顶点数'],
      ['vertices', '顶点数'],
      ['number of faces', '面数'],
      ['faces', '面数'],
      ['total', '总耗时'],
      ['shape generation', '形体生成'],
      ['texture generation', '材质生成'],
      ['face reduction', '网格简化'],
      ['convert textured obj to glb', '材质转换']
    ];
    const found = aliases.find(([key]) => lower.includes(key));
    return found ? found[1] : name.replace(/^time\s*·\s*/i, '');
  }

  function friendlyStatValue(name, value) {
    if (typeof value === 'number') {
      if (/time|takes|generation|reduction|convert|total/i.test(name)) return value.toFixed(value >= 10 ? 1 : 2) + ' 秒';
      return new Intl.NumberFormat('zh-CN').format(value);
    }
    return String(value);
  }

  function renderStats(stats) {
    elements.statsRaw.textContent = stats ? JSON.stringify(stats, null, 2) : '暂无数据';
    const rows = flattenStats(stats).slice(0, 9);
    elements.statsGrid.replaceChildren();
    if (!rows.length) {
      const empty = document.createElement('p');
      empty.className = 'panel-hint';
      empty.textContent = '本次生成没有返回网格统计。';
      elements.statsGrid.appendChild(empty);
      return;
    }
    rows.forEach(([name, value]) => {
      const card = document.createElement('div');
      card.className = 'stat-card';
      const label = document.createElement('span');
      label.textContent = friendlyStatName(name);
      const strong = document.createElement('strong');
      strong.textContent = friendlyStatValue(name, value);
      card.append(label, strong);
      elements.statsGrid.appendChild(card);
    });
  }

  function renderGeneratedDownloads(result) {
    elements.generatedDownloads.replaceChildren();
    const links = [];
    if (result.shape_download) links.push(['形体原始结果', result.shape_download, 'GLB']);
    if (result.textured_download) links.push(['带材质原始结果', result.textured_download, 'GLB']);
    links.forEach(([label, href, meta]) => {
      const anchor = document.createElement('a');
      anchor.className = 'download-link';
      anchor.href = href;
      anchor.textContent = label;
      const span = document.createElement('span');
      span.textContent = meta;
      anchor.appendChild(span);
      elements.generatedDownloads.appendChild(anchor);
    });
    elements.generatedDownloads.hidden = !links.length;
  }

  function applyGenerationResult(result) {
    state.generationResult = result;
    state.exportResult = null;
    elements.generatedViewer.innerHTML = result.viewer_html || '';
    elements.exportViewer.replaceChildren();
    elements.resultMode.textContent = result.mode === 'textured' ? '形体与材质' : '形体草稿';
    elements.resultViews.textContent = result.view_count ? result.view_count + ' 个方向' : '—';
    elements.resultSeed.textContent = result.seed == null ? '—' : String(result.seed);
    elements.resultFiles.textContent = result.has_textured ? '形体、材质模型' : result.has_shape ? '形体模型' : '未返回文件';
    renderStats(result.stats);
    renderGeneratedDownloads(result);
    elements.exportButton.disabled = !result.has_shape;
    elements.includeTexture.disabled = !result.has_textured;
    elements.textureExportRow.classList.toggle('muted-control', !result.has_textured);
    elements.textureExportHelp.textContent = result.has_textured ? '本次结果包含 PBR 材质' : '仅带材质结果可用';
    if (!result.has_textured) elements.includeTexture.checked = false;
    elements.downloadButton.hidden = true;
    const exportTab = $('.view-tab[data-view="export"]');
    exportTab.disabled = true;
    activateView('generated');
  }

  async function pollJob(jobId, onSuccess, busyKind) {
    while (true) {
      await new Promise((resolve) => window.setTimeout(resolve, 1200));
      let response;
      try {
        response = await fetch('/api/jobs/' + encodeURIComponent(jobId), { cache: 'no-store' });
      } catch (error) {
        throw new Error('Beta 页面服务连接中断。');
      }
      if (!response.ok) throw new Error('无法读取任务状态。');
      const job = await response.json();
      if (job.status === 'queued') {
        setJobStatus('等待处理', job.status_text || '等待本地生成服务', 'warn');
        continue;
      }
      if (job.status === 'running') {
        setJobStatus(busyKind === 'export' ? '正在导出' : '正在生成', job.status_text || '本地模型正在处理', 'info');
        continue;
      }
      if (job.status === 'succeeded') {
        onSuccess(job.result || {});
        return;
      }
      if (job.status === 'failed') throw new Error(job.error || job.status_text || '任务失败');
      throw new Error('收到未知任务状态。');
    }
  }

  async function startGeneration() {
    if (!state.files.front || !state.serviceOnline || state.generating) return;
    state.generating = true;
    state.exportResult = null;
    elements.downloadButton.hidden = true;
    setBusyOverlay(true, state.mode === 'textured' ? '正在生成形体与材质' : '正在生成形体草稿', '本地多视图模型正在联合处理各方向图片，请保持服务窗口开启。');
    setJobStatus('正在提交', '正在把多视图参考交给本地生成服务', 'info');
    updateGenerateAvailability();
    const form = new FormData();
    VIEW_KEYS.forEach((view) => {
      const file = state.files[view];
      if (file) form.append(view + '_image', file, file.name);
    });
    form.append('params', JSON.stringify({
      mode: state.mode,
      remove_background: elements.removeBackground.checked,
      randomize_seed: elements.randomSeed.checked,
      seed: Number(elements.seedInput.value || 1234),
      steps: Number(elements.stepsInput.value || 30),
      guidance_scale: Number(elements.guidanceInput.value || 5),
      octree_resolution: Number(elements.octreeInput.value || 256),
      num_chunks: Number(elements.chunksInput.value || 8000)
    }));
    try {
      const response = await fetch('/api/generate', { method: 'POST', body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || '无法创建生成任务。');
      state.generationJobId = payload.id;
      setJobStatus('等待处理', payload.status_text || '任务已进入队列', 'warn');
      await pollJob(payload.id, (result) => {
        applyGenerationResult(result);
        setJobStatus('生成完成', '三维资产草稿已生成，可以检查并导出。', 'ok');
        toast('三维资产草稿已生成。', 'ok');
      }, 'generation');
    } catch (error) {
      setJobStatus('生成失败', error.message || '本地模型没有完成任务。', 'err');
      toast(error.message || '生成失败。', 'err');
    } finally {
      state.generating = false;
      setBusyOverlay(false);
      updateGenerateAvailability();
    }
  }

  async function startExport() {
    if (!state.generationJobId || !state.generationResult || state.exporting) return;
    state.exporting = true;
    elements.exportButton.disabled = true;
    elements.downloadButton.hidden = true;
    setBusyOverlay(true, '正在转换导出文件', '本次操作只生成本地副本，不会写入 OntoTwin 主工具。');
    setJobStatus('正在导出', '正在转换所选文件格式', 'info');
    try {
      const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_job_id: state.generationJobId,
          file_type: elements.fileType.value,
          simplify: elements.simplifyMesh.checked,
          include_texture: elements.includeTexture.checked,
          target_faces: Number(elements.targetFaces.value || 10000)
        })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || '无法创建导出任务。');
      await pollJob(payload.id, (result) => {
        state.exportResult = result;
        elements.exportViewer.innerHTML = result.viewer_html || '';
        elements.downloadButton.href = result.download;
        elements.downloadButton.hidden = false;
        const exportTab = $('.view-tab[data-view="export"]');
        exportTab.disabled = false;
        activateView('export');
        setJobStatus('导出完成', result.file_type.toUpperCase() + ' 文件已准备好。', 'ok');
        toast('导出文件已准备好。', 'ok');
      }, 'export');
    } catch (error) {
      setJobStatus('导出失败', error.message || '本地服务没有完成转换。', 'err');
      toast(error.message || '导出失败。', 'err');
    } finally {
      state.exporting = false;
      setBusyOverlay(false);
      elements.exportButton.disabled = !state.generationResult;
      updateGenerateAvailability();
    }
  }

  async function recoverLatestResult() {
    if (state.generating || state.exporting || state.recovering) return;
    state.recovering = true;
    updateGenerateAvailability();
    setJobStatus('正在恢复', '正在读取最近一次混元多视图输出', 'info');
    try {
      const response = await fetch('/api/recover-latest', { method: 'POST' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || '无法恢复最近一次本地结果。');
      state.generationJobId = payload.id;
      applyGenerationResult(payload.result || {});
      setJobStatus('已恢复结果', '最近一次本地模型已恢复，可以下载或转换导出。', 'ok');
      toast('已恢复最近一次本地生成结果。', 'ok');
    } catch (error) {
      setJobStatus('恢复失败', error.message || '没有找到可恢复的模型文件。', 'err');
      toast(error.message || '恢复失败。', 'err');
    } finally {
      state.recovering = false;
      updateGenerateAvailability();
    }
  }

  async function loadExamples() {
    elements.exampleGrid.innerHTML = '<div class="skeleton-card"></div><div class="skeleton-card"></div><div class="skeleton-card"></div>';
    try {
      const response = await fetch('/api/examples', { cache: 'no-store' });
      if (!response.ok) throw new Error('示例加载失败');
      const payload = await response.json();
      elements.exampleGrid.replaceChildren();
      if (!payload.items || !payload.items.length) {
        const empty = document.createElement('p');
        empty.className = 'panel-hint';
        empty.textContent = '当前混元目录没有示例图片。';
        elements.exampleGrid.appendChild(empty);
        return;
      }
      payload.items.slice(0, 9).forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'example-card';
        button.setAttribute('aria-label', '使用示例图片 ' + item.name);
        const image = document.createElement('img');
        image.src = item.url;
        image.alt = '';
        image.loading = 'lazy';
        button.appendChild(image);
        button.addEventListener('click', async () => {
          try {
            const exampleResponse = await fetch(item.url, { cache: 'no-store' });
            const blob = await exampleResponse.blob();
            setViewFile('front', new File([blob], item.name, { type: blob.type || 'image/png' }));
            toast('示例图片已载入正面视图。', 'ok');
          } catch (error) {
            toast('无法载入这张示例图片。', 'err');
          }
        });
        elements.exampleGrid.appendChild(button);
      });
    } catch (error) {
      elements.exampleGrid.replaceChildren();
      const empty = document.createElement('p');
      empty.className = 'panel-hint';
      empty.textContent = '示例图片暂不可用，请上传自己的参考图片。';
      elements.exampleGrid.appendChild(empty);
    }
  }

  function bindEvents() {
    elements.sidebarToggle.addEventListener('click', () => {
      const collapsed = !elements.sidebar.classList.contains('collapsed');
      elements.sidebar.classList.toggle('collapsed', collapsed);
      elements.sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
      elements.sidebarToggle.setAttribute('aria-label', collapsed ? '展开侧栏' : '收起侧栏');
      elements.sidebarToggle.dataset.tip = collapsed ? '展开侧栏' : '收起侧栏';
      try { localStorage.setItem('ontotwin.reverse.sidebar', collapsed ? 'collapsed' : 'open'); } catch (error) {}
    });
    $$('[data-inactive-nav]').forEach((button) => button.addEventListener('click', () => {
      toast(button.dataset.inactiveNav + '仅用于展示主工具菜单，本 Beta 不执行跳转。');
    }));
    elements.servicePill.addEventListener('click', () => checkService(true));
    VIEW_KEYS.forEach((view) => {
      const controls = viewElements[view];
      controls.upload.addEventListener('click', () => controls.input.click());
      controls.upload.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          controls.input.click();
        }
      });
      controls.input.addEventListener('change', () => setViewFile(view, controls.input.files && controls.input.files[0]));
      controls.clear.addEventListener('click', () => clearView(view));
      ['dragenter', 'dragover'].forEach((name) => controls.upload.addEventListener(name, (event) => {
        event.preventDefault();
        controls.upload.classList.add('dragover');
      }));
      ['dragleave', 'drop'].forEach((name) => controls.upload.addEventListener(name, (event) => {
        event.preventDefault();
        controls.upload.classList.remove('dragover');
      }));
      controls.upload.addEventListener('drop', (event) => setViewFile(view, event.dataTransfer.files && event.dataTransfer.files[0]));
    });
    elements.clearAllViews.addEventListener('click', clearAllViews);
    $$('.segment').forEach((button) => button.addEventListener('click', () => setMode(button.dataset.mode)));
    elements.randomSeed.addEventListener('change', () => {
      elements.seedInput.disabled = elements.randomSeed.checked;
    });
    elements.stepsInput.addEventListener('input', () => { elements.stepsValue.textContent = elements.stepsInput.value; });
    elements.octreeInput.addEventListener('input', () => { elements.octreeValue.textContent = elements.octreeInput.value; });
    elements.simplifyMesh.addEventListener('change', () => { elements.targetFacesRow.hidden = !elements.simplifyMesh.checked; });
    elements.generateButton.addEventListener('click', startGeneration);
    elements.exportButton.addEventListener('click', startExport);
    elements.recoverButton.addEventListener('click', recoverLatestResult);
    $$('.view-tab').forEach((button) => button.addEventListener('click', () => activateView(button.dataset.view)));
    elements.refreshExamples.addEventListener('click', loadExamples);
  }

  function restoreSidebar() {
    let collapsed = false;
    try { collapsed = localStorage.getItem('ontotwin.reverse.sidebar') === 'collapsed'; } catch (error) {}
    elements.sidebar.classList.toggle('collapsed', collapsed);
    elements.sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
    elements.sidebarToggle.setAttribute('aria-label', collapsed ? '展开侧栏' : '收起侧栏');
    elements.sidebarToggle.dataset.tip = collapsed ? '展开侧栏' : '收起侧栏';
  }

  bindEvents();
  restoreSidebar();
  setMode('shape');
  updateGenerateAvailability();
  checkService(false);
  loadExamples();
})();
