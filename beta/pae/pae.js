(function () {
  'use strict';

  const STORAGE_KEY = 'pae.beta.draft.v1';
  const SCHEMA_VERSION = 'pae.behavior.v1';

  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const uid = (prefix) => prefix + '_' + Math.random().toString(36).slice(2, 9);
  const finiteOr = (value, fallback) => Number.isFinite(Number(value)) ? Number(value) : fallback;
  const slugify = (value) => String(value || 'animation').trim().toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/gi, '-').replace(/^-+|-+$/g, '') || 'animation';
  const packageIdFor = (title) => 'pkg_pae_beta_' + slugify(title).slice(0, 28) + '_' + Math.random().toString(36).slice(2, 6);

  const actionCatalog = {
    appear: { name: '出现', channel: 'transform', capability: 'visibility', glyph: '+' },
    move: { name: '移动', channel: 'transform', capability: 'transform', glyph: '↔' },
    rotate: { name: '旋转', channel: 'transform', capability: 'transform', glyph: 'R' },
    scale: { name: '缩放', channel: 'transform', capability: 'transform', glyph: 'S' },
    hold: { name: '等待', channel: 'transform', capability: 'timeline', glyph: '||' },
    flash: { name: '闪烁', channel: 'fx', capability: 'fx', glyph: 'FX' },
    label: { name: '字幕', channel: 'label', capability: 'label', glyph: 'A' },
    material: { name: '材质变体', channel: 'material', capability: 'material', glyph: 'M' }
  };

  const library = [
    { id: 'lib.appear', name: '出现', kind: 'appear', type: '基础动作', description: '从透明到可见', asset_ref: 'primitive.appear' },
    { id: 'lib.move', name: '平移到位', kind: 'move', type: '基础动作', description: '从起点移动到终点', asset_ref: 'primitive.move' },
    { id: 'lib.rotate', name: '轴向旋转', kind: 'rotate', type: '基础动作', description: '按指定轴旋转', asset_ref: 'primitive.rotate' },
    { id: 'lib.scale', name: '缩放', kind: 'scale', type: '基础动作', description: '按关键帧缩放', asset_ref: 'primitive.scale' },
    { id: 'lib.hold', name: '保持', kind: 'hold', type: '基础动作', description: '在时间轴上保持状态', asset_ref: 'primitive.hold' },
    { id: 'lib.flash', name: '警示闪烁', kind: 'flash', type: '效果占位', description: '供 A 角路由连接特效实现', asset_ref: 'fx.warning.flash' },
    { id: 'lib.material', name: '材质变体', kind: 'material', type: '效果占位', description: '切换逻辑材质键', asset_ref: 'material.variant' },
    { id: 'lib.label', name: '步骤字幕', kind: 'label', type: '说明辅助', description: '显示说明块文本', asset_ref: 'primitive.label' }
  ];

  const templates = [
    {
      id: 'template.process.v1',
      name: '工序流程',
      shortName: '工序',
      description: '适用于有明确工艺顺序、标准和工位的说明。',
      sourceKind: 'OA / SOP',
      defaultTitle: '轴承装配工序说明',
      generator: 'process',
      meta: { series: 'F0522', station: '装配工位 03', revision: 'R2' },
      steps: [
        { id: 'step.p010', code: 'P010', name: '提供零件', category: '物料', kind: 'sequence', description: '将连杆与轴承送至装配位置。', standard: 'CP2202 带安装槽轴衬和衬套的安装装配车间操作法', targets: ['rod', 'bearing-left', 'bearing-right'] },
        { id: 'step.p020', code: 'P020', name: '检验', category: '检验', kind: 'sequence', description: '确认零件型号、方向和外观状态。', standard: '来料检验记录 · 外观与尺寸', targets: ['rod'] },
        { id: 'step.p030', code: 'P030', name: '安装轴承', category: '装配', kind: 'sequence', description: '按工序图样在连杆上安装轴承，并对轴承座进行翻遍。', standard: 'CP2202 · 轴承安装标准', targets: ['bearing-left', 'bearing-right', 'rod'] },
        { id: 'step.p040', code: 'P040', name: '复检与标识', category: '质量', kind: 'sequence', description: '完成复检并保留可追溯标识。', standard: '出厂标识与质量门', targets: ['label', 'assembly'] }
      ]
    },
    {
      id: 'template.assembly.v1',
      name: '装配步骤',
      shortName: '装配',
      description: '适用于零件到位、定位、固定等装配演示。',
      sourceKind: '装配说明',
      defaultTitle: '连杆组件装配说明',
      generator: 'assembly',
      meta: { assembly: '连杆组件', station: '装配工位 03', revision: 'v1.0' },
      steps: [
        { id: 'step.a01', code: 'A01', name: '物料到位', category: '准备', kind: 'sequence', description: '连杆与轴承进入装配基座的受控槽位。', standard: '装配准备检查表', targets: ['rod', 'bearing-left', 'bearing-right'] },
        { id: 'step.a02', code: 'A02', name: '定位轴承', category: '定位', kind: 'sequence', description: '调整轴承方向，使其与连杆中心对齐。', standard: '定位基准：中心轴', targets: ['bearing-left', 'bearing-right'] },
        { id: 'step.a03', code: 'A03', name: '固定组件', category: '固定', kind: 'sequence', description: '完成固定并显示组件说明标签。', standard: '紧固检查与标识', targets: ['rod', 'label'] }
      ]
    },
    {
      id: 'template.state.v1',
      name: '状态演示',
      shortName: '状态',
      description: '适用于待机、运行、故障等持续状态表现。',
      sourceKind: '状态说明',
      defaultTitle: '设备运行状态说明',
      generator: 'state',
      meta: { objectType: '工业设备', station: '演示场景', revision: 'v1.0' },
      steps: [
        { id: 'step.s01', code: 'S01', name: '待机', category: '主状态', kind: 'state', description: '设备保持安全静止姿态，等待启动。', standard: '状态字：idle', targets: ['assembly'] },
        { id: 'step.s02', code: 'S02', name: '运行', category: '主状态', kind: 'state', description: '设备进入运行状态，中心部件按速度参数旋转。', standard: '状态字：running', targets: ['rod'] },
        { id: 'step.s03', code: 'S03', name: '故障', category: '主状态', kind: '状态修饰', description: '停止运动并显示警示表现，等待人工确认。', standard: '状态字：fault', targets: ['assembly', 'label'] }
      ]
    }
  ];

  const objects = [
    { id: 'assembly', name: '装配基座', type: '父级模型', slot: 'primary', asset_ref: 'model.assembly.base', mock_asset: 'assembly-base', capabilities: ['visibility', 'transform', 'material', 'fx'], description: '承载组件的主模型' },
    { id: 'rod', name: '连杆组件', type: '可动部件', slot: 'named:rod', asset_ref: 'model.rod.assembly', mock_asset: 'rod-linkage', capabilities: ['visibility', 'transform', 'material'], description: '支持移动、旋转和材质表现' },
    { id: 'bearing-left', name: '左侧轴承', type: '可动部件', slot: 'named:bearing_left', asset_ref: 'model.bearing.standard', mock_asset: 'bearing-ring', capabilities: ['visibility', 'transform'], description: '支持旋转和定位' },
    { id: 'bearing-right', name: '右侧轴承', type: '可动部件', slot: 'named:bearing_right', asset_ref: 'model.bearing.standard', mock_asset: 'bearing-ring', capabilities: ['visibility', 'transform'], description: '支持旋转和定位' },
    { id: 'tool', name: '装配工具', type: '辅助对象', slot: 'named:tool', asset_ref: 'model.tool.fixture', mock_asset: 'fixture-tool', capabilities: ['visibility', 'transform'], description: '可选的辅助对象' },
    { id: 'label', name: '步骤字幕', type: '说明对象', slot: 'label', asset_ref: 'primitive.label', mock_asset: 'annotation-panel', capabilities: ['visibility', 'label', 'transform'], description: '显示当前说明块文本' }
  ];

  let state = createInitialState('template.assembly.v1');
  let history = [];
  let future = [];
  let playing = false;
  let rafId = null;
  let lastFrame = 0;
  let inspectorTab = 'object';
  let libraryTab = 'all';
  let draggedLibraryId = null;
  let autoSaveTimer = null;
  let stageTool = 'select';
  let stageDrag = null;
  // Only a validation result produced for the current editable payload may
  // authorize export.  This is intentionally kept outside the persisted
  // manifest so an old/local draft cannot accidentally reuse a stale result.
  let validationFingerprint = null;

  // The Beta editor owns a small dependency-free 3D viewport.  It renders
  // procedural mock assets on a canvas so the interaction can be exercised
  // offline without loading UE or a production asset registry.
  const camera3d = {
    yaw: -0.72,
    pitch: 0.48,
    distance: 760,
    target: { x: 0, y: 0, z: 85 },
    panX: 0,
    panY: 0
  };
  const renderer3d = {
    canvas: null,
    ctx: null,
    width: 0,
    height: 0,
    dpr: 1,
    projectedObjects: [],
    resizeObserver: null
  };
  const meshCache3d = new Map();

  function getTemplate(id) {
    return templates.find((item) => item.id === id) || templates[0];
  }

  function specIdForTemplate(template) {
    const prefix = ({ process: 'PROCESS', assembly: 'ASM', state: 'STATE' })[template && template.generator] || 'GENERIC';
    return 'SPEC-' + prefix + '-001';
  }

  function findTemplate(id) {
    return templates.find((item) => item.id === id) || null;
  }

  function getObject(id) {
    return (Array.isArray(state.objects) ? state.objects : []).find((item) => item && item.id === id) || null;
  }

  function objectBound(object) {
    return !!object && typeof object.slot === 'string' && object.slot.trim() !== '' && typeof object.asset_ref === 'string' && object.asset_ref.trim() !== '';
  }

  function controlledSlotShape(slot) {
    const value = String(slot || '').trim();
    return value === 'primary' || value === 'label' || value === 'status_indicator' || value === 'alarm' || /^(named|motion):[a-z0-9_.:-]+$/i.test(value);
  }

  function objectName(object, fallbackId) {
    return object && object.name ? object.name : (fallbackId || '未命名对象');
  }

  function objectCapabilities(object) {
    if (!object) return [];
    if (Array.isArray(object.capabilities)) return object.capabilities;
    return objectBound(object) ? ['visibility', 'transform', 'material', 'fx', 'label'] : [];
  }

  function createInitialState(templateId) {
    const template = getTemplate(templateId);
    const specId = specIdForTemplate(template);
    return {
      schema_version: SCHEMA_VERSION,
      package_id: packageIdFor(template.defaultTitle),
      package_name: slugify(template.defaultTitle),
      template_id: template.id,
      template_name: template.name,
      source: {
        id: specId,
        title: template.defaultTitle,
        kind: template.sourceKind,
        version: '1.0',
        revision: template.meta.revision || 'v1.0',
        origin: 'PAE Beta 内置示例'
      },
      spec: {
        id: specId,
        title: template.defaultTitle,
        template_id: template.id,
        meta: clone(template.meta),
        steps: clone(template.steps)
      },
      objects: clone(objects),
      tracks: [],
      duration_s: 12,
      export_range: 'all',
      export_format: 'behavior-package-v1',
      stage_offset: { x: 0, y: 0 },
      selectedStepId: template.steps[0].id,
      selectedObjectId: template.steps[0].targets[0] || 'assembly',
      selectedClipId: null,
      playhead_s: 0,
      grid: true,
      status: 'draft',
      dirty: false,
      validation: null,
      collapsedGroups: {},
      manualEdits: [],
      lastSavedAt: null
    };
  }

  function activeTemplate() {
    return getTemplate(state.template_id);
  }

  function currentStep() {
    return state.spec.steps.find((step) => step.id === state.selectedStepId) || state.spec.steps[0];
  }

  function allClips() {
    return (Array.isArray(state.tracks) ? state.tracks : []).reduce((result, track) => result.concat(track && Array.isArray(track.clips) ? track.clips : []), []);
  }

  function selectedClip() {
    return allClips().find((clip) => clip.id === state.selectedClipId) || null;
  }

  function clipTrack(clipId) {
    return state.tracks.find((track) => (track.clips || []).some((clip) => clip.id === clipId)) || null;
  }

  function formatTime(seconds, decimals) {
    const value = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(value / 60).toString().padStart(2, '0');
    const fraction = decimals === 0 ? Math.floor(value % 60).toString().padStart(2, '0') : (value % 60).toFixed(decimals).padStart(decimals + 3, '0');
    return minutes + ':' + fraction;
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function actionName(kind) {
    return (actionCatalog[kind] || { name: kind }).name;
  }

  function channelName(channel) {
    return ({ transform: '运动', fx: '特效', material: '材质', label: '字幕' })[channel] || channel;
  }

  function toast(message, type) {
    const root = $('#toastRoot');
    const item = document.createElement('div');
    item.className = 'toast-item' + (type ? ' ' + type : '');
    item.textContent = message;
    root.appendChild(item);
    window.setTimeout(() => item.remove(), 2800);
  }

  function buildValidationFingerprint() {
    try {
      return JSON.stringify({
        template_id: state.template_id,
        spec: state.spec,
        objects: state.objects,
        tracks: state.tracks,
        duration_s: state.duration_s,
        export_range: state.export_range,
        export_format: state.export_format,
        selected_clip_for_export: state.export_range === 'selected' ? state.selectedClipId : null
      });
    } catch (error) {
      return null;
    }
  }

  function invalidateValidation() {
    state.validation = null;
    validationFingerprint = null;
    if (state.status === 'validated' || state.status === 'blocked') state.status = 'draft';
  }

  function markDirty(message) {
    invalidateValidation();
    state.dirty = true;
    if (message) $('#footerMessage').textContent = message;
    updateSaveState();
    scheduleAutoSave();
  }

  function scheduleAutoSave() {
    if (autoSaveTimer) window.clearTimeout(autoSaveTimer);
    autoSaveTimer = window.setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      } catch (error) {
        // Manual save will surface the error; background recovery stays best-effort.
      }
      autoSaveTimer = null;
    }, 650);
  }

  function updateSaveState() {
    const chip = $('#saveState');
    if (!chip) return;
    const status = state.dirty ? '未保存' : '已保存';
    const dotClass = state.dirty ? 'status-dot-warn' : 'status-dot-ok';
    chip.innerHTML = '<span class="status-dot ' + dotClass + '"></span>' + status;
  }

  function pushHistory() {
    history.push(clone(state));
    if (history.length > 40) history.shift();
    future = [];
  }

  function undo() {
    if (!history.length) {
      toast('没有可撤销的修改', 'warn');
      return;
    }
    future.push(clone(state));
    state = history.pop();
    invalidateValidation();
    stopPlayback();
    renderAll();
    toast('已撤销上一项修改', 'ok');
  }

  function redo() {
    if (!future.length) {
      toast('没有可重做的修改', 'warn');
      return;
    }
    history.push(clone(state));
    state = future.pop();
    invalidateValidation();
    renderAll();
    toast('已恢复修改', 'ok');
  }

  function setView(viewName) {
    $$('.tab').forEach((tab) => {
      const active = tab.dataset.view === viewName;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    ['source', 'editor', 'export'].forEach((name) => {
      const view = $('#view-' + name);
      if (!view) return;
      view.hidden = name !== viewName;
      view.classList.toggle('active', name === viewName);
    });
    if (viewName === 'export') renderExport();
    if (viewName === 'editor') {
      renderTimeline();
      applyPreview();
    }
  }

  function renderTemplateList() {
    const root = $('#templateList');
    root.innerHTML = templates.map((template) => {
      const active = template.id === state.template_id ? ' active' : '';
      return '<button class="template-card' + active + '" data-template="' + escapeHtml(template.id) + '">' +
        '<span class="template-card-title">' + escapeHtml(template.name) + '</span>' +
        '<span class="template-card-desc">' + escapeHtml(template.description) + '</span>' +
        '<span class="template-card-meta">' + escapeHtml(template.sourceKind) + ' · ' + template.steps.length + ' 个说明块</span>' +
      '</button>';
    }).join('');
  }

  function renderSourceMeta() {
    const template = activeTemplate();
    const source = state.source;
    $('#projectName').textContent = state.source.title + ' · Beta 样例';
    $('#sourceTitle').textContent = source.title;
    $('#sourceMeta').textContent = source.id + ' · v' + source.version + ' · ' + state.spec.steps.length + ' 个模块';
    $('#structureTitle').textContent = template.name + '结构';
    $('#structureType').textContent = template.name + '模板';
    $('#structureDescription').textContent = template.description;
    $('#stageTitle').textContent = source.title + ' · 动画草稿';
    $('#exportTemplateName').textContent = template.name;
    $('#exportTemplateId').textContent = template.id;
    $('#packageName').value = state.package_name;
  }

  function renderStructure() {
    const root = $('#structureCanvas');
    const template = activeTemplate();
    const groupKey = 'root.' + template.id;
    const collapsed = !!state.collapsedGroups[groupKey];
    const nodes = state.spec.steps.map((step) => {
      const selected = step.id === state.selectedStepId ? ' selected' : '';
      const hasClips = allClips().some((clip) => clip.step_id === step.id);
      const stateLabel = hasClips ? '已生成草稿' : '待生成';
      return '<div class="structure-node' + selected + '" data-structure-node="' + escapeHtml(step.id) + '" tabindex="0">' +
        '<div class="node-code">' + escapeHtml(step.code || '—') + '</div>' +
        '<div class="node-main"><div class="node-name">' + escapeHtml(step.name) + '</div><div class="node-caption">' + escapeHtml(step.description || '未填写说明') + '</div></div>' +
        '<div class="node-kind">' + escapeHtml(step.category || '说明') + '<br><span class="muted">' + stateLabel + '</span></div>' +
      '</div>';
    }).join('');
    root.innerHTML = '<div class="structure-root"><div class="structure-group"><div class="structure-group-header" data-structure-group="' + escapeHtml(groupKey) + '"><span class="structure-caret">' + (collapsed ? '▸' : '▾') + '</span><span class="structure-group-title">' + escapeHtml(state.source.title) + '</span><span class="structure-group-meta">' + state.spec.steps.length + ' 个说明块</span></div><div class="structure-children' + (collapsed ? ' collapsed' : '') + '">' + nodes + '</div></div></div>';
  }

  function nodeStatus(stepId) {
    const clips = allClips().filter((clip) => clip.step_id === stepId);
    if (!clips.length) return { label: '待生成', dot: 'status-dot-warn' };
    const invalid = clips.some((clip) => !clip || !clip.target_ref || clip.end_s <= clip.start_s || !objectBound(getObject(clip.target_ref)) || typeof clip.asset_ref !== 'string' || !clip.asset_ref.trim());
    if (invalid) return { label: '需修复', dot: 'status-dot-err' };
    return { label: '已生成', dot: 'status-dot-ok' };
  }

  function renderNodeDetail() {
    const step = currentStep();
    if (!step) return;
    const status = nodeStatus(step.id);
    $('#nodeDetailTitle').textContent = (step.code ? step.code + ' ' : '') + step.name;
    $('#nodeDetailStatus').innerHTML = '<span class="status-dot ' + status.dot + '"></span>' + status.label;
    $('#nodeDetailBody').innerHTML =
      '<div class="detail-field"><span class="detail-label">说明类别</span><span class="detail-value">' + escapeHtml(step.category || '通用说明') + '</span></div>' +
      '<div class="detail-field"><span class="detail-label">来源说明</span><div class="detail-description">' + escapeHtml(step.description || '暂无说明文本') + '</div></div>' +
      '<div class="detail-field"><span class="detail-label">标准 / 参考</span><span class="detail-value">' + escapeHtml(step.standard || '未填写') + '</span></div>' +
      '<div class="detail-field"><span class="detail-label">依赖</span><span class="detail-value">' + (step.depends_on && step.depends_on.length ? escapeHtml(step.depends_on.join('、')) : '按当前顺序执行') + '</span></div>';
    const bindings = (step.targets || []).map((targetId) => {
      const target = getObject(targetId);
      const bound = objectBound(target);
      return '<div class="binding-item"><div class="binding-icon">' + (bound ? 'O' : '?') + '</div><div class="binding-copy"><strong>' + escapeHtml(objectName(target, targetId)) + '</strong><span>' + escapeHtml(bound ? target.slot : '未绑定槽位') + '</span></div><span class="status-dot ' + (bound ? 'status-dot-ok' : 'status-dot-err') + '"></span></div>';
    }).join('');
    $('#nodeBindings').innerHTML = bindings || '<div class="detail-description">此说明块暂未指定目标对象。</div>';
  }

  function renderEditorSteps() {
    const root = $('#editorSteps');
    root.innerHTML = state.spec.steps.map((step) => {
      const status = nodeStatus(step.id);
      const selected = step.id === state.selectedStepId ? ' selected' : '';
      return '<div class="editor-step' + selected + '" data-editor-step="' + escapeHtml(step.id) + '"><span class="editor-step-code">' + escapeHtml(step.code || '—') + '</span><span class="editor-step-copy"><strong>' + escapeHtml(step.name) + '</strong><span>' + escapeHtml(step.category || '说明') + '</span></span><span class="editor-step-state ' + (status.dot === 'status-dot-ok' ? 'ready' : '') + '"></span></div>';
    }).join('');
  }

  function renderEditorObjects() {
    const root = $('#editorObjects');
    root.innerHTML = state.objects.map((object) => {
      const selected = object.id === state.selectedObjectId ? ' selected' : '';
      const count = allClips().filter((clip) => clip.target_ref === object.id).length;
      const boundClass = objectBound(object) ? '' : ' unbound';
      return '<div class="object-row' + selected + boundClass + '" data-object-id="' + escapeHtml(object.id) + '"><span class="object-bullet"></span><span>' + escapeHtml(objectName(object, object.id)) + '</span><small>' + (objectBound(object) ? count : '未绑定') + '</small></div>';
    }).join('');
  }

  function ensureTrack(targetId, channel) {
    let track = state.tracks.find((item) => item.target_ref === targetId && item.channel === channel);
    if (!track) {
      const target = getObject(targetId);
      track = { id: uid('track'), target_ref: targetId, target_name: objectName(target, targetId), channel: channel, clips: [] };
      state.tracks.push(track);
    }
    return track;
  }

  function makeKeyframes(kind, params, duration) {
    const end = Number(duration) || 1;
    if (kind === 'move') {
      return [{ t_s: 0, position_cm: clone(params.from || { x: -120, y: 0, z: 0 }) }, { t_s: end, position_cm: clone(params.to || { x: 0, y: 0, z: 0 }) }];
    }
    if (kind === 'rotate') {
      return [{ t_s: 0, rotation_deg: 0 }, { t_s: end, rotation_deg: Number(params.angle || 90) }];
    }
    if (kind === 'scale') {
      return [{ t_s: 0, scale: Number(params.fromScale || 0.75) }, { t_s: end, scale: Number(params.toScale || 1) }];
    }
    if (kind === 'appear') {
      return [{ t_s: 0, value: 0 }, { t_s: end, value: 1 }];
    }
    if (kind === 'flash') {
      return [{ t_s: 0, value: 0 }, { t_s: end * .25, value: 1 }, { t_s: end * .5, value: 0 }, { t_s: end * .75, value: 1 }, { t_s: end, value: 0 }];
    }
    return [{ t_s: 0, value: 1 }, { t_s: end, value: 1 }];
  }

  function makeClip(step, kind, targetId, start, duration, extra, metadata) {
    const action = actionCatalog[kind] || actionCatalog.hold;
    const options = extra || {};
    const rawParams = Object.assign({}, options, options.params || {});
    delete rawParams.params;
    const defaults = kind === 'move' ? { from: { x: -120, y: 0, z: 0 }, to: { x: 0, y: 0, z: 0 } }
      : kind === 'rotate' ? { angle: 90, axis: 'Z' }
      : kind === 'scale' ? { fromScale: .75, toScale: 1 }
      : (kind === 'label' || kind === 'material') ? { value: step ? step.description : '' }
      : {};
    const params = Object.assign(defaults, rawParams);
    const assetRef = params.asset_ref || action.asset_ref || ('primitive.' + kind);
    delete params.asset_ref;
    const clip = {
      id: uid('clip'),
      behavior_id: 'behavior.' + (state.template_id.split('.').slice(1, -1).join('.') || 'generic') + '.' + (step ? step.code : 'custom') + '.' + kind,
      behavior_version: '1.0',
      step_id: step ? step.id : null,
      name: (step ? step.name + ' · ' : '') + action.name,
      kind: kind,
      channel: action.channel,
      target_ref: targetId,
      asset_ref: assetRef,
      required_capabilities: [action.capability],
      source_process_id: state.spec ? state.spec.id : null,
      source_block_id: step ? step.id : null,
      start_s: Number(start.toFixed(2)),
      end_s: Number((start + duration).toFixed(2)),
      event_id: metadata && metadata.event_id ? String(metadata.event_id) : null,
      easing: metadata && metadata.easing ? String(metadata.easing) : 'ease-in-out',
      loop: metadata && metadata.loop != null ? !!metadata.loop : false,
      enabled: metadata && metadata.enabled != null ? metadata.enabled !== false : true,
      params: params,
      keyframes: makeKeyframes(kind, params, duration),
      generated: true,
      manual: false
    };
    return clip;
  }

  function normalizeActionKind(value) {
    const raw = String(value || '').trim().toLowerCase();
    const aliases = { appear: 'appear', show: 'appear', move: 'move', translate: 'move', translation: 'move', rotate: 'rotate', rotation: 'rotate', scale: 'scale', hold: 'hold', wait: 'hold', flash: 'flash', blink: 'flash', label: 'label', subtitle: 'label', material: 'material' };
    return aliases[raw] || (Object.prototype.hasOwnProperty.call(actionCatalog, raw) ? raw : null);
  }

  function resolvePlanTarget(step, preferred, index) {
    const candidates = Array.isArray(step && step.targets) ? step.targets.filter(Boolean) : [];
    // An explicit action target is authoritative. Never silently substitute
    // the first listed target when a structured action names another object.
    if (preferred) return preferred;
    if (!candidates.length) return 'assembly';
    return candidates[index % candidates.length];
  }

  function actionPlan(step, index, generator) {
    if (step && Array.isArray(step.actions) && step.actions.length) {
      return step.actions.map((item, actionIndex) => {
        const kind = normalizeActionKind(item && (item.kind || item.action || item.type));
        if (!kind) return null;
        const duration = finiteOr(item.duration_s != null ? item.duration_s : item.duration, 1.5);
        const extra = Object.assign({}, item.params || {}, item.extra || {});
        if (item.asset_ref) extra.asset_ref = item.asset_ref;
        return {
          kind: kind,
          target: resolvePlanTarget(step, item.target || item.target_ref, actionIndex),
          duration: Math.max(.1, duration),
          start_s: Number.isFinite(Number(item.start_s)) ? Number(item.start_s) : null,
          parallel: !!item.parallel,
          event_id: item.event_id || item.id || null,
          easing: item.easing || null,
          loop: item.loop,
          enabled: item.enabled,
          extra: extra
        };
      }).filter(Boolean);
    }
    if (generator === 'process') {
      if (index === 0) return [{ kind: 'appear', target: 'rod', duration: 1.1 }, { kind: 'move', target: 'rod', duration: 2.1, extra: { from: { x: -150, y: 0, z: 0 }, to: { x: 0, y: 0, z: 0 } } }];
      if (index === 1) return [{ kind: 'hold', target: 'rod', duration: 1.5 }, { kind: 'label', target: 'label', duration: 1.5, extra: { value: step.description } }];
      if (index === 2) return [{ kind: 'rotate', target: 'bearing-left', duration: 2.2, extra: { angle: 180 } }, { kind: 'rotate', target: 'bearing-right', duration: 2.2, extra: { angle: 180 } }, { kind: 'move', target: 'rod', duration: 1.4, extra: { from: { x: 0, y: 0, z: 0 }, to: { x: 12, y: 0, z: 0 } } }];
      return [{ kind: 'label', target: 'label', duration: 1.8, extra: { value: step.description } }, { kind: 'flash', target: 'assembly', duration: 1.8 }];
    }
    if (generator === 'state') {
      if (index === 0) return [{ kind: 'hold', target: 'assembly', duration: 2.5 }, { kind: 'label', target: 'label', duration: 2.5, extra: { value: '待机 · 安全静止姿态' } }];
      if (index === 1) return [{ kind: 'rotate', target: 'rod', duration: 4.2, extra: { angle: 360 } }, { kind: 'label', target: 'label', duration: 4.2, extra: { value: '运行 · speed = 0.82' } }];
      return [{ kind: 'flash', target: 'assembly', duration: 2.2 }, { kind: 'material', target: 'assembly', duration: 2.2, extra: { value: 'warning' } }, { kind: 'label', target: 'label', duration: 2.2, extra: { value: '故障 · 等待人工确认' } }];
    }
    if (index === 0) return [{ kind: 'appear', target: 'rod', duration: 1.1 }, { kind: 'move', target: 'rod', duration: 2.1, extra: { from: { x: -130, y: 0, z: 0 }, to: { x: 0, y: 0, z: 0 } } }];
    if (index === 1) return [{ kind: 'rotate', target: 'bearing-left', duration: 1.8, extra: { angle: 90 } }, { kind: 'rotate', target: 'bearing-right', duration: 1.8, extra: { angle: -90 } }];
    return [{ kind: 'move', target: 'rod', duration: 1.5, extra: { from: { x: 0, y: 0, z: 0 }, to: { x: 0, y: 0, z: 6 } } }, { kind: 'label', target: 'label', duration: 1.5, extra: { value: '已固定 · 可交付' } }];
  }

  function generateDraft(force) {
    if (!force && state.tracks.length) {
      openModal({
        title: '重新生成动画草稿',
        body: '<p>重新生成只会替换标记为“自动生成”的片段；<strong>manual=true</strong> 的人工片段和未标记为自动生成的片段会保留。若新旧片段发生重叠，请在时间轴中复核。</p>',
        actions: [
          { text: '取消', className: 'btn btn-ghost', close: true },
          { text: '继续生成', className: 'btn btn-primary', close: true, onClick: () => generateDraft(true) }
        ]
      });
      return;
    }
    pushHistory();
    const template = activeTemplate();
    // Regeneration is deliberately conservative: only clips explicitly
    // marked as generated are replaced.  Manual clips (and legacy/imported
    // clips without a generated flag) remain intact so a new template pass
    // cannot silently discard human work.
    const preservedTracks = state.tracks.map((track) => ({
      id: track.id,
      target_ref: track.target_ref,
      target_name: track.target_name,
      channel: track.channel,
      clips: (track.clips || []).filter((clip) => clip.manual === true || clip.generated !== true)
    })).filter((track) => track.clips.length);
    const previousSelectedClipId = state.selectedClipId;
    state.tracks = preservedTracks;
    state.manualEdits = (state.manualEdits || []).filter((clipId) => allClips().some((clip) => clip.id === clipId));
    let cursor = 0;
    state.spec.steps.forEach((step, index) => {
      const plan = actionPlan(step, index, template.generator);
      const stepStart = cursor;
      let stepEnd = cursor;
      plan.forEach((item, itemIndex) => {
        const targetId = resolvePlanTarget(step, item.target, itemIndex);
        const start = item.start_s != null ? Math.max(0, item.start_s) : (item.parallel ? stepStart : cursor);
        const clip = makeClip(step, item.kind, targetId, start, item.duration, item.extra, item);
        // Preserve source-level parallel intent explicitly for downstream
        // consumers; equal timestamps alone are not enough to infer a group.
        clip.parallel = !!item.parallel;
        clip.parallel_group = item.parallel && step && step.id ? step.id + ':parallel' : null;
        const track = ensureTrack(targetId, clip.channel);
        track.clips.push(clip);
        const end = start + item.duration;
        stepEnd = Math.max(stepEnd, end);
        if (!item.parallel && item.start_s == null) cursor = Math.min(end, 59);
      });
      cursor = Math.min(Math.max(cursor, stepEnd) + .35, 59);
    });
    const preservedEnd = allClips().reduce((max, clip) => {
      const end = Number(clip.end_s);
      return Number.isFinite(end) ? Math.max(max, end) : max;
    }, 0);
    const previousDuration = Number(state.duration_s);
    state.duration_s = Math.max(
      8,
      Number.isFinite(previousDuration) ? previousDuration : 0,
      Math.ceil(cursor + .5),
      Math.ceil(preservedEnd + .5)
    );
    const selectedStillExists = previousSelectedClipId && allClips().some((clip) => clip.id === previousSelectedClipId);
    state.selectedClipId = selectedStillExists ? previousSelectedClipId : (allClips()[0] ? allClips()[0].id : null);
    state.playhead_s = 0;
    state.status = 'draft';
    markDirty('已生成动画草稿，请确认对象、轴向和时长');
    renderAll();
    setView('editor');
    toast('已按“' + template.name + '”生成动画草稿', 'ok');
  }

  function addCustomClip(kind, targetId, stepId, startOverride, extra) {
    const step = state.spec.steps.find((item) => item.id === stepId) || currentStep();
    const target = targetId || state.selectedObjectId || 'assembly';
    const channel = (actionCatalog[kind] || actionCatalog.hold).channel;
    pushHistory();
    const track = ensureTrack(target, channel);
    const lastEnd = track.clips.reduce((max, clip) => Math.max(max, clip.end_s), state.playhead_s);
    const duration = kind === 'label' ? 2 : 1.5;
    const requestedStart = startOverride == null ? lastEnd : finiteOr(startOverride, lastEnd);
    const start = startOverride == null ? Math.min(lastEnd, Math.max(0, state.duration_s - .5)) : Math.max(0, requestedStart);
    const clipExtra = Object.assign({}, extra || {});
    if (kind === 'label' && clipExtra.value == null) clipExtra.value = step ? step.description : '';
    const clip = makeClip(step, kind, target, start, duration, clipExtra);
    clip.generated = false;
    clip.manual = true;
    track.clips.push(clip);
    state.selectedClipId = clip.id;
    state.selectedObjectId = target;
    state.manualEdits.push(clip.id);
    state.duration_s = Math.max(state.duration_s, clip.end_s + .5);
    markDirty('已添加动作：' + actionName(kind));
    renderAll();
    setView('editor');
  }

  function selectStep(stepId) {
    if (!state.spec.steps.some((step) => step.id === stepId)) return;
    state.selectedStepId = stepId;
    const step = currentStep();
    if (step && step.targets && step.targets[0]) state.selectedObjectId = step.targets[0];
    renderAll();
  }

  function selectObject(objectId) {
    if (!state.objects.some((item) => item.id === objectId)) return;
    state.selectedObjectId = objectId;
    inspectorTab = 'object';
    renderEditorObjects();
    renderInspectors();
    applyPreview();
  }

  function selectClip(clipId) {
    const clip = allClips().find((item) => item.id === clipId);
    if (!clip) return;
    state.selectedClipId = clipId;
    state.selectedStepId = clip.step_id || state.selectedStepId;
    state.selectedObjectId = clip.target_ref || state.selectedObjectId;
    inspectorTab = 'clip';
    renderEditorSteps();
    renderEditorObjects();
    renderTimeline();
    renderInspectors();
    applyPreview();
  }

  function renderTimeline() {
    const labels = $('#timelineLabels');
    const ruler = $('#timelineRuler');
    const tracksRoot = $('#timelineTracks');
    const duration = Math.max(1, state.duration_s);
    const tickCount = Math.max(6, Math.ceil(duration / 2));
    ruler.innerHTML = Array.from({ length: tickCount + 1 }, (_, index) => {
      const value = Math.min(duration, index * (duration / tickCount));
      return '<span class="ruler-tick" style="left:' + (value / duration * 100) + '%">' + formatTime(value, 0) + '</span>';
    }).join('');
    labels.innerHTML = state.tracks.length ? state.tracks.map((track) => '<div class="timeline-label"><strong>' + escapeHtml(track.target_name) + '</strong><span class="muted"> · ' + escapeHtml(channelName(track.channel)) + '</span></div>').join('') : '<div class="timeline-label muted">尚无动作轨道</div>';
    tracksRoot.innerHTML = state.tracks.length ? state.tracks.map((track) => {
      const clips = (track.clips || []).slice().sort((a, b) => finiteOr(a.start_s, 0) - finiteOr(b.start_s, 0));
      const clipsHtml = clips.map((clip) => {
        const selected = clip.id === state.selectedClipId ? ' selected' : '';
        const start = finiteOr(clip.start_s, 0);
        const end = finiteOr(clip.end_s, start + .1);
        const left = clamp(start / duration * 100, 0, 100);
        const width = clamp((end - start) / duration * 100, 1.3, Math.max(1.3, 100 - left));
        return '<div class="timeline-clip' + selected + '" data-clip-id="' + escapeHtml(clip.id) + '" data-channel="' + escapeHtml(clip.channel) + '" aria-label="' + escapeHtml(clip.name) + '" style="left:' + left + '%;width:' + width + '%">' + escapeHtml(actionName(clip.kind)) + '</div>';
      }).join('');
      return '<div class="timeline-track-row" data-track-id="' + escapeHtml(track.id) + '" data-drop-target="true">' + clipsHtml + '</div>';
    }).join('') : '<div class="timeline-track-row"><span class="muted" style="padding:12px;display:block;font-size:11px">从右侧素材库添加动作，或先生成动画草稿。</span></div>';
    const playhead = $('#playhead');
    playhead.style.left = (clamp(state.playhead_s / duration, 0, 1) * 100) + '%';
    $('#playheadReadout').textContent = formatTime(state.playhead_s, 1);
    $('#durationReadout').textContent = formatTime(duration, 1);
  }

  function renderObjectInspector() {
    const root = $('#inspector-object');
    const object = getObject(state.selectedObjectId);
    if (!object) {
      root.innerHTML = '<div class="empty-inspector"><div class="eyebrow">目标对象</div><h3>请选择对象</h3><p class="inspector-note">对象来自结构化说明或导入文件。</p></div>';
      return;
    }
    const clips = allClips().filter((clip) => clip.target_ref === object.id);
    const bound = objectBound(object);
    root.innerHTML = '<div class="inspector-block"><div class="eyebrow">目标对象</div><h3>' + escapeHtml(objectName(object, object.id)) + '</h3><p class="inspector-note">' + escapeHtml(object.description || '来自结构化说明的对象引用') + '</p><span class="small-status"><span class="status-dot ' + (bound ? 'status-dot-ok' : 'status-dot-err') + '"></span>' + (bound ? '已绑定' : '待绑定') + '</span></div>' +
 '<div class="inspector-block"><div class="eyebrow">绑定信息</div><div class="property-grid"><label class="form-row"><span class="label">受控槽位</span><input class="field" data-object-field="slot" value="' + escapeHtml(object.slot || '') + '" placeholder="例如 named:rod"></label><label class="form-row"><span class="label">逻辑资产</span><input class="field" data-object-field="asset_ref" value="' + escapeHtml(object.asset_ref || '') + '" placeholder="例如 model.part"></label></div><div class="detail-field"><span class="detail-label">3D mock 类型</span><span class="detail-value">' + escapeHtml(object.mock_asset || assetKind3d(object)) + '</span></div><p class="panel-hint">留空会在校验时阻断导出，避免静默错绑。mock 类型只影响 Beta 预览，导出只保留识别标签。</p></div>' +
      '<div class="inspector-block"><div class="eyebrow">当前动作</div><div class="binding-list" style="padding:0">' + (clips.length ? clips.map((clip) => '<button class="binding-item" data-clip-id="' + escapeHtml(clip.id) + '"><div class="binding-icon">' + escapeHtml((actionCatalog[clip.kind] || {}).glyph || '·') + '</div><div class="binding-copy"><strong>' + escapeHtml(actionName(clip.kind)) + '</strong><span>' + formatTime(clip.start_s, 1) + ' – ' + formatTime(clip.end_s, 1) + '</span></div></button>').join('') : '<div class="detail-description">还没有绑定动作。可以从素材库点击一个动作添加。</div>') + '</div></div>' +
      '<button class="btn btn-secondary full-width" data-action="open-library">从素材库添加动作</button>';
  }

  function renderLibraryInspector() {
    const root = $('#inspector-library');
    const filtered = library.filter((item) => libraryTab === 'all' || item.kind === libraryTab);
    const tabs = ['all'].concat(Object.keys(actionCatalog));
    root.innerHTML = '<div class="library-toolbar"><input class="field" data-library-search placeholder="搜索动作或效果" aria-label="搜索素材"></div>' +
      '<div class="library-tabs">' + tabs.map((tab) => '<button class="library-tab' + (libraryTab === tab ? ' active' : '') + '" data-library-tab="' + tab + '">' + (tab === 'all' ? '全部' : actionName(tab)) + '</button>').join('') + '</div>' +
      '<p class="inspector-note">素材只保存逻辑引用；A 角或 UE 执行层负责寻找实际实现。</p>' +
      '<div class="library-card-grid">' + filtered.map((item) => '<button class="library-card" draggable="true" data-library-id="' + escapeHtml(item.id) + '"><div class="library-thumb">' + escapeHtml((actionCatalog[item.kind] || {}).glyph || '·') + '</div><strong>' + escapeHtml(item.name) + '</strong><span>' + escapeHtml(item.description) + '</span></button>').join('') + '</div>';
  }

  function keyframeValueEditor(frame, index) {
    const field = (path, value, label, type) => '<label class="kf-value"><span>' + label + '</span><input aria-label="' + label + '" class="field" type="' + (type || 'number') + '" step="0.1" data-kf-index="' + index + '" data-kf-field="' + path + '" value="' + escapeHtml(value == null ? '' : value) + '"></label>';
    if (frame.position_cm) return '<div class="keyframe-values">' + field('position_cm.x', frame.position_cm.x, 'X') + field('position_cm.y', frame.position_cm.y, 'Y') + field('position_cm.z', frame.position_cm.z, 'Z') + '</div>';
    if (frame.rotation_deg != null) return '<div class="keyframe-values">' + field('rotation_deg', frame.rotation_deg, '角度') + '</div>';
    if (frame.scale != null) return '<div class="keyframe-values">' + field('scale', frame.scale, '比例') + '</div>';
    return '<div class="keyframe-values">' + field('value', frame.value == null ? 1 : frame.value, '值', typeof frame.value === 'number' ? 'number' : 'text') + '</div>';
  }

  function keyframeType(frame) {
    return frame.position_cm ? '位置' : frame.rotation_deg != null ? '旋转' : frame.scale != null ? '缩放' : '值';
  }

  function renderClipInspector() {
    const root = $('#inspector-clip');
    const clip = selectedClip();
    if (!clip) {
      root.innerHTML = '<div class="empty-inspector"><div class="eyebrow">动作属性</div><h3>请选择时间轴片段</h3><p class="inspector-note">点击一个片段，或从素材库添加基础动作。</p></div>';
      return;
    }
    const params = clip.params || {};
    const from = params.from || { x: 0, y: 0, z: 0 };
    const to = params.to || { x: 0, y: 0, z: 0 };
    const keyframes = (clip.keyframes || []).map((frame, index) => '<tr><td>' + index + '</td><td><input aria-label="关键帧时间" type="number" step="0.1" data-kf-index="' + index + '" data-kf-field="t_s" value="' + escapeHtml(frame.t_s) + '"></td><td><span>' + keyframeType(frame) + '</span>' + keyframeValueEditor(frame, index) + '</td><td><button class="btn btn-ghost btn-sm" data-delete-kf="' + index + '"' + ((clip.keyframes || []).length <= 2 ? ' disabled' : '') + '>删除</button></td></tr>').join('');
    root.innerHTML = '<div class="inspector-block"><div class="eyebrow">动作属性</div><h3>' + escapeHtml(actionName(clip.kind)) + '</h3><p class="inspector-note">' + escapeHtml(clip.behavior_id) + '</p></div>' +
      '<div class="inspector-block"><div class="property-grid"><label class="form-row"><span class="label">动作名称</span><input class="field" data-clip-field="name" value="' + escapeHtml(clip.name) + '"></label><label class="form-row"><span class="label">动作类型</span><input class="field" value="' + escapeHtml(actionName(clip.kind)) + '" disabled></label><label class="form-row"><span class="label">开始（秒）</span><input class="field" type="number" step="0.1" min="0" data-clip-field="start_s" value="' + clip.start_s + '"></label><label class="form-row"><span class="label">结束（秒）</span><input class="field" type="number" step="0.1" min="0" data-clip-field="end_s" value="' + clip.end_s + '"></label><label class="form-row"><span class="label">缓动</span><select class="field" data-clip-field="easing"><option ' + (clip.easing === 'linear' ? 'selected' : '') + '>linear</option><option ' + (clip.easing === 'ease-in' ? 'selected' : '') + '>ease-in</option><option ' + (clip.easing === 'ease-in-out' ? 'selected' : '') + '>ease-in-out</option></select></label><label class="form-row"><span class="label">循环</span><span style="display:flex;align-items:center;height:32px"><input type="checkbox" data-clip-field="loop" ' + (clip.loop ? 'checked' : '') + '> <span class="muted" style="margin-left:6px">持续循环</span></span></label></div></div>' +
      '<div class="inspector-block"><div class="eyebrow">参数</div>' + (clip.kind === 'move' ? '<div class="property-grid"><label class="form-row"><span class="label">起点 X（cm）</span><input class="field" type="number" data-param="from.x" value="' + from.x + '"></label><label class="form-row"><span class="label">终点 X（cm）</span><input class="field" type="number" data-param="to.x" value="' + to.x + '"></label><label class="form-row"><span class="label">起点 Y（cm）</span><input class="field" type="number" data-param="from.y" value="' + from.y + '"></label><label class="form-row"><span class="label">终点 Y（cm）</span><input class="field" type="number" data-param="to.y" value="' + to.y + '"></label><label class="form-row"><span class="label">起点 Z（cm）</span><input class="field" type="number" data-param="from.z" value="' + finiteOr(from.z, 0) + '"></label><label class="form-row"><span class="label">终点 Z（cm）</span><input class="field" type="number" data-param="to.z" value="' + finiteOr(to.z, 0) + '"></label></div>' : clip.kind === 'rotate' ? '<div class="property-grid"><label class="form-row"><span class="label">旋转角度（度）</span><input class="field" type="number" data-param="angle" value="' + (params.angle || 0) + '"></label><label class="form-row"><span class="label">旋转轴</span><select class="field" data-param="axis"><option ' + (params.axis === 'X' ? 'selected' : '') + '>X</option><option ' + (params.axis === 'Y' ? 'selected' : '') + '>Y</option><option ' + (params.axis === 'Z' || !params.axis ? 'selected' : '') + '>Z</option></select></label></div>' : clip.kind === 'label' || clip.kind === 'material' ? '<label class="form-row"><span class="label">逻辑值</span><input class="field" data-param="value" value="' + escapeHtml(params.value || '') + '"></label>' : '<p class="inspector-note">该动作使用默认参数，可通过关键帧调整时序。</p>') + '</div>' +
      '<div class="inspector-block"><div class="eyebrow">关键帧</div><table class="keyframe-table"><thead><tr><th>#</th><th>时间</th><th>类型</th><th></th></tr></thead><tbody>' + keyframes + '</tbody></table><button class="btn btn-secondary btn-sm" data-action="add-keyframe" style="margin-top:8px">添加中间关键帧</button></div>' +
      '<button class="btn btn-danger full-width" data-action="delete-clip">删除动作片段</button>';
  }

  function renderInspectors() {
    ['object', 'library', 'clip'].forEach((name) => {
      const section = $('#inspector-' + name);
      const tab = $('.inspector-tab[data-inspector="' + name + '"]');
      const active = inspectorTab === name;
      section.hidden = !active;
      section.classList.toggle('active', active);
      tab.classList.toggle('active', active);
    });
    renderObjectInspector();
    renderLibraryInspector();
    renderClipInspector();
  }

  function renderStoryBoard() {
    const root = $('#storyboard');
    root.innerHTML = state.spec.steps.map((step) => {
      const clips = allClips().filter((clip) => clip.step_id === step.id).sort((a, b) => a.start_s - b.start_s);
      const start = clips.length ? Math.min.apply(null, clips.map((clip) => clip.start_s)) : 0;
      const end = clips.length ? Math.max.apply(null, clips.map((clip) => clip.end_s)) : 0;
      return '<div class="story-row"><div class="story-code">' + escapeHtml(step.code || '—') + '</div><div class="story-copy"><strong>' + escapeHtml(step.name) + '</strong><span>' + escapeHtml(clips.length ? clips.map((clip) => actionName(clip.kind)).join(' · ') : '尚未生成动作') + '</span></div><div class="story-duration">' + (clips.length ? formatTime(start, 1) + '–' + formatTime(end, 1) : '—') + '</div></div>';
    }).join('');
  }

  function getExportRange() {
    const duration = Math.max(0, finiteOr(state.duration_s, 0));
    if (state.export_range === 'selected') {
      const clip = selectedClip() || allClips()[0];
      if (clip) return [clamp(finiteOr(clip.start_s, 0), 0, duration), clamp(finiteOr(clip.end_s, duration), 0, duration)];
    }
    return [0, duration];
  }

  function buildManifest() {
    const range = getExportRange();
    const tracks = state.tracks.map((track) => {
      const target = getObject(track.target_ref);
      const clips = (track.clips || []).filter((clip) => finiteOr(clip.end_s, 0) >= range[0] && finiteOr(clip.start_s, 0) <= range[1]).map((clip) => ({
        id: clip.id,
        behavior_id: clip.behavior_id,
        behavior_version: clip.behavior_version,
        event_id: clip.event_id || null,
        source_spec_id: clip.source_process_id || (state.spec && state.spec.id) || null,
        source_process_id: clip.source_process_id || (state.spec && state.spec.id) || null,
        source_block_id: clip.source_block_id || clip.step_id || null,
        step_id: clip.step_id,
        kind: clip.kind,
        target_ref: clip.target_ref,
        target_slot: target && target.slot ? target.slot : null,
        required_capabilities: clone(clip.required_capabilities || ((actionCatalog[clip.kind] || {}).capability ? [(actionCatalog[clip.kind] || {}).capability] : [])),
        asset_ref: clip.asset_ref,
        start_s: clip.start_s,
        end_s: clip.end_s,
        easing: clip.easing,
        loop: clip.loop,
        enabled: clip.enabled,
        params: clone(clip.params || {}),
        keyframes: clone(clip.keyframes || []),
        parallel: !!clip.parallel,
        parallel_group: clip.parallel_group || null,
        generated: !!clip.generated,
        manual: !!clip.manual
      }));
      return {
        id: track.id,
        target_ref: track.target_ref,
        target_slot: target && target.slot ? target.slot : null,
        bound: objectBound(target),
        channel: track.channel,
        clips: clips
      };
    }).filter((track) => track.clips.length);
    const requiredCapabilities = Array.from(new Set(tracks.flatMap((track) => track.clips.flatMap((clip) => clip.required_capabilities || []))));
    const spec = state.spec || { id: null, title: '', steps: [] };
    return {
      schema_version: SCHEMA_VERSION,
      package_id: state.package_id,
      package_name: state.package_name,
      behavior_id: 'package.' + state.package_id,
      behavior_version: '1.0',
      template: { id: state.template_id, name: state.template_name },
      source: clone(state.source),
      source_spec_id: spec.id,
      target: {
        object_type_id: (spec.meta && (spec.meta.object_type_id || spec.meta.object_type)) || 'demo.assembly.component',
        coordinate_system: 'OT_CM',
        unit: { distance: 'cm', rotation: 'deg' }
      },
      source_process_id: spec.id,
      required_capabilities: requiredCapabilities,
      spec: { id: spec.id, title: spec.title, steps: clone(spec.steps || []) },
      // `process` is retained as a compatibility alias for the original OA
      // prototype; `spec` is the generic field for every template.
      process: { id: spec.id, title: spec.title, steps: clone(spec.steps || []) },
      objects: (Array.isArray(state.objects) ? state.objects : []).map((object) => ({ id: object.id, name: objectName(object, object.id), type: object.type, target_slot: object.slot || null, asset_ref: object.asset_ref || null, mock_asset: object.mock_asset || assetKind3d(object), capabilities: clone(object.capabilities || []), bound: objectBound(object) })),
      tracks: tracks,
      defaults: { camera: 'fixed', subtitle: 'source_step.description', fallback: 'static_pose' },
      validation: clone(state.validation || { status: 'unvalidated', issues: [] }),
      export: { format: state.export_format || 'behavior-package-v1', duration_s: finiteOr(state.duration_s, 0), range_s: range, clip_count: tracks.reduce((sum, track) => sum + track.clips.length, 0) }
    };
  }

  function buildStoryboardPayload() {
    const range = getExportRange();
    return {
      schema_version: 'pae.storyboard.v1',
      package_id: state.package_id,
      package_name: state.package_name,
      source: clone(state.source),
      source_spec_id: state.spec && state.spec.id ? state.spec.id : null,
      template: { id: state.template_id, name: state.template_name },
      range_s: range,
      storyboard: (state.spec.steps || []).map((step) => ({
        source_block_id: step.id,
        code: step.code,
        name: step.name,
        description: step.description,
        actions: allClips().filter((clip) => clip.step_id === step.id && finiteOr(clip.end_s, 0) >= range[0] && finiteOr(clip.start_s, 0) <= range[1]).map((clip) => ({ event_id: clip.event_id || null, behavior_id: clip.behavior_id, kind: clip.kind, target_ref: clip.target_ref, start_s: clip.start_s, end_s: clip.end_s, parallel: !!clip.parallel, parallel_group: clip.parallel_group || null }))
      }))
    };
  }

  function buildARouteSample() {
    const range = getExportRange();
    const clip = allClips().filter((item) => finiteOr(item.end_s, 0) >= range[0] && finiteOr(item.start_s, 0) <= range[1]).slice().sort((a, b) => a.start_s - b.start_s)[0];
    if (!clip) return null;
    const target = getObject(clip.target_ref);
    return {
      behavior_id: clip.behavior_id,
      behavior_version: clip.behavior_version,
      event_id: clip.event_id || null,
      source_spec_id: clip.source_process_id || (state.spec && state.spec.id) || null,
      source_process_id: clip.source_process_id || (state.spec && state.spec.id) || null,
      source_block_id: clip.source_block_id || clip.step_id || null,
      kind: clip.kind,
      asset_ref: clip.asset_ref,
      target_ref: clip.target_ref,
      target_slot: target && target.slot ? target.slot : null,
      required_capabilities: clone(clip.required_capabilities || []),
      params: clone(clip.params || {}),
      fallback: 'static_pose'
    };
  }

  function renderARouteSample() {
    const root = $('#aRoutePreview');
    if (!root) return;
    const sample = buildARouteSample();
    root.textContent = sample ? JSON.stringify(sample, null, 2) : '先运行校验并生成动作…';
  }

  function validationIsCurrent() {
    if (!state.validation || !validationFingerprint) return false;
    const currentFingerprint = buildValidationFingerprint();
    return !!currentFingerprint && currentFingerprint === validationFingerprint;
  }

  function renderExport() {
    const manifest = buildManifest();
    const clips = manifest.tracks.reduce((result, track) => result.concat(track.clips || []), []);
    $('#exportClipCount').textContent = clips.length;
    $('#exportObjectCount').textContent = new Set(clips.map((clip) => clip.target_ref)).size;
    if ($('#exportRange')) $('#exportRange').value = state.export_range || 'all';
    if ($('#exportFormat')) $('#exportFormat').value = state.export_format || 'behavior-package-v1';
    renderStoryBoard();
    $('#manifestPreview').textContent = JSON.stringify(manifest, null, 2);
    renderARouteSample();
    const status = $('#exportStatus');
    const download = $('#downloadBtn');
    if (!state.validation) {
      status.innerHTML = '<span class="status-dot status-dot-warn"></span>尚未校验';
      download.disabled = true;
      $('#validationList').innerHTML = '<div class="validation-item warning"><span class="status-dot status-dot-warn"></span><span>请先运行校验，确认行为包可以交付给 A 角。</span></div>';
      return;
    }
    if (!validationIsCurrent()) {
      status.innerHTML = '<span class="status-dot status-dot-warn"></span>需要重新校验';
      download.disabled = true;
      $('#validationList').innerHTML = '<div class="validation-item warning"><span class="status-dot status-dot-warn"></span><span>内容已变化，旧校验结果已失效。请重新运行校验。</span></div>';
      return;
    }
    const hasError = state.validation.issues.some((issue) => issue.level === 'error');
    status.innerHTML = '<span class="status-dot ' + (hasError ? 'status-dot-err' : 'status-dot-ok') + '"></span>' + (hasError ? '存在阻断项' : '可导出');
    download.disabled = hasError;
    $('#validationList').innerHTML = state.validation.issues.map((issue) => '<div class="validation-item ' + issue.level + '"><span class="status-dot ' + (issue.level === 'error' ? 'status-dot-err' : issue.level === 'warning' ? 'status-dot-warn' : 'status-dot-ok') + '"></span><span>' + escapeHtml(issue.message) + '</span></div>').join('');
  }

  function renderAll() {
    renderTemplateList();
    renderSourceMeta();
    renderStructure();
    renderNodeDetail();
    renderEditorSteps();
    renderEditorObjects();
    renderTimeline();
    renderInspectors();
    renderExport();
    updateSaveState();
    applyPreview();
  }

  function saveDraft() {
    try {
      if (autoSaveTimer) window.clearTimeout(autoSaveTimer);
      autoSaveTimer = null;
      state.lastSavedAt = new Date().toISOString();
      state.dirty = false;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      updateSaveState();
      $('#footerMessage').textContent = '草稿已保存到本机';
      toast('草稿已保存，可在刷新后恢复', 'ok');
    } catch (error) {
      toast('保存失败：浏览器不允许本地存储', 'err');
    }
  }

  function loadDraft() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return false;
      const saved = JSON.parse(raw);
      if (!saved || saved.schema_version !== SCHEMA_VERSION || !saved.spec || !findTemplate(saved.template_id)) return false;
      state = Object.assign(createInitialState(saved.template_id), saved);
      if (!state.spec || typeof state.spec !== 'object') state.spec = clone(createInitialState(saved.template_id).spec);
      state.objects = Array.isArray(state.objects) ? state.objects.map((item) => normalizeObjectRecord(item)).filter(Boolean) : clone(objects);
      state.tracks = Array.isArray(state.tracks) ? state.tracks.filter((track) => track && typeof track === 'object').map((track) => Object.assign({ id: uid('track'), target_ref: '', target_name: track.target_ref || '未命名对象', channel: 'transform', clips: [] }, track, { clips: Array.isArray(track.clips) ? track.clips.filter(Boolean) : [] })) : [];
      state.spec.steps = Array.isArray(state.spec.steps) ? state.spec.steps : [];
      // Validation is an in-memory, current-editor result.  A persisted
      // result may have been produced by an older validator or before a
      // browser-side edit, so require an explicit fresh run after restore.
      invalidateValidation();
      return true;
    } catch (error) {
      return false;
    }
  }

  function resetDemo() {
    openModal({
      title: '恢复内置样例',
      body: '<p>这会清除当前 Beta 本地草稿并恢复“装配步骤”样例。若当前内容尚未导出，请先保存或下载需要保留的文件。</p>',
      actions: [
        { text: '取消', className: 'btn btn-ghost', close: true },
          { text: '恢复样例', className: 'btn btn-primary', close: true, onClick: () => { history = []; future = []; if (autoSaveTimer) window.clearTimeout(autoSaveTimer); autoSaveTimer = null; try { localStorage.removeItem(STORAGE_KEY); } catch (error) { /* recovery can continue without storage */ } state = createInitialState('template.assembly.v1'); markDirty('已恢复内置样例，请重新运行校验'); renderAll(); setView('source'); toast('已恢复内置样例', 'ok'); } }
      ]
    });
  }

  function switchTemplate(templateId) {
    const template = getTemplate(templateId);
    if (template.id === state.template_id) return;
    if (state.dirty || state.tracks.length) {
      openModal({
        title: '切换动画模板',
        body: '<p>切换模板会清空当前说明的动画轨道和未保存的结构改动。请确认已保存需要保留的版本。</p>',
        actions: [
          { text: '取消', className: 'btn btn-ghost', close: true },
          { text: '切换模板', className: 'btn btn-primary', close: true, onClick: () => switchTemplateNow(template.id) }
        ]
      });
      return;
    }
    switchTemplateNow(template.id);
  }

  function switchTemplateNow(templateId) {
    pushHistory();
    const template = getTemplate(templateId);
    state.template_id = template.id;
    state.template_name = template.name;
    state.source = { id: specIdForTemplate(template), title: template.defaultTitle, kind: template.sourceKind, version: '1.0', revision: template.meta.revision || 'v1.0', origin: 'PAE Beta 内置示例' };
    state.spec = { id: state.source.id, title: template.defaultTitle, template_id: template.id, meta: clone(template.meta), steps: clone(template.steps) };
    state.package_id = packageIdFor(template.defaultTitle);
    state.package_name = slugify(template.defaultTitle);
    state.tracks = [];
    state.selectedStepId = template.steps[0].id;
    state.selectedObjectId = template.steps[0].targets[0] || 'assembly';
    state.selectedClipId = null;
    state.playhead_s = 0;
    state.export_range = 'all';
    state.export_format = 'behavior-package-v1';
    state.stage_offset = { x: 0, y: 0 };
    state.validation = null;
    markDirty('已切换模板，可生成新的动画草稿');
    renderAll();
    toast('已切换到“' + template.name + '”模板', 'ok');
  }

  function addValidationIssue(issues, level, message) {
    if (!issues.some((issue) => issue.level === level && issue.message === message)) {
      issues.push({ level: level, message: message });
    }
  }

  function readFiniteValidationNumber(value, label, issues) {
    const isString = typeof value === 'string';
    const isNumber = typeof value === 'number';
    if ((!isString && !isNumber) || (isString && !value.trim())) {
      addValidationIssue(issues, 'error', label + '必须是有限数字。');
      return null;
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      addValidationIssue(issues, 'error', label + '不能是 NaN 或 Infinity。');
      return null;
    }
    return numeric;
  }

  function collectNonFiniteNumbers(value, path, issues, seen) {
    if (typeof value === 'number') {
      if (!Number.isFinite(value)) addValidationIssue(issues, 'error', path + '不能是 NaN 或 Infinity。');
      return;
    }
    if (!value || typeof value !== 'object') return;
    if (seen.has(value)) return;
    seen.add(value);
    if (Array.isArray(value)) {
      value.forEach((item, index) => collectNonFiniteNumbers(item, path + '[' + index + ']', issues, seen));
      return;
    }
    Object.keys(value).forEach((key) => collectNonFiniteNumbers(value[key], path + '.' + key, issues, seen));
  }

  function runValidation() {
    const issues = [];
    const clips = allClips();
    const objectsList = Array.isArray(state.objects) ? state.objects : [];
    const objectIds = new Set(objectsList.map((object) => object && object.id));
    const steps = state.spec && Array.isArray(state.spec.steps) ? state.spec.steps : [];
    const duration = readFiniteValidationNumber(state.duration_s, '时间轴总时长', issues);

    if (!Array.isArray(state.objects)) addValidationIssue(issues, 'error', '对象绑定列表格式无效。');
    if (!clips.length) addValidationIssue(issues, 'error', '没有动作片段，至少生成或添加一个动作。');

    clips.forEach((clip, clipIndex) => {
      const kind = clip && clip.kind;
      const label = (clip && clip.name) || actionName(kind) || ('片段 #' + (clipIndex + 1));
      const hasKnownKind = !!kind && Object.prototype.hasOwnProperty.call(actionCatalog, kind);
      if (!hasKnownKind) addValidationIssue(issues, 'error', '动作“' + label + '”使用了未知动作类型。');

      if (!clip || typeof clip !== 'object') {
        addValidationIssue(issues, 'error', '动作片段 #' + (clipIndex + 1) + ' 数据格式无效。');
        return;
      }

      if (typeof clip.asset_ref !== 'string' || !clip.asset_ref.trim()) {
        addValidationIssue(issues, 'error', '动作“' + label + '”缺少 asset_ref。');
      }

      const start = readFiniteValidationNumber(clip.start_s, '动作“' + label + '”的开始时间', issues);
      const end = readFiniteValidationNumber(clip.end_s, '动作“' + label + '”的结束时间', issues);
      if (start != null && start < 0) addValidationIssue(issues, 'error', '动作“' + label + '”的开始时间不能小于 0。');
      if (start != null && end != null && !(end > start)) addValidationIssue(issues, 'error', '动作“' + label + '”的结束时间必须大于开始时间。');
      if (duration != null && end != null && end > duration + .01) addValidationIssue(issues, 'error', '动作“' + label + '”超出时间轴范围。');

      const target = objectsList.find((object) => object && object.id === clip.target_ref);
      if (!objectIds.has(clip.target_ref)) {
        addValidationIssue(issues, 'error', '动作“' + label + '”没有有效目标对象。');
      } else if (!objectBound(target)) {
        if (!target || typeof target.slot !== 'string' || !target.slot.trim()) addValidationIssue(issues, 'error', '动作“' + label + '”的目标对象缺少受控槽位。');
        if (!target || typeof target.asset_ref !== 'string' || !target.asset_ref.trim()) addValidationIssue(issues, 'error', '动作“' + label + '”的目标对象缺少逻辑资产 asset_ref。');
      } else {
        if (!controlledSlotShape(target.slot)) addValidationIssue(issues, 'warning', '动作“' + label + '”使用了未注册的槽位命名空间，导出前需由 A 角适配器确认映射。');
        const required = (actionCatalog[kind] || {}).capability;
        if (required && required !== 'timeline' && !objectCapabilities(target).includes(required)) {
          addValidationIssue(issues, 'error', '动作“' + label + '”与目标对象能力不兼容：缺少 ' + required + '。');
        }
      }
      if (typeof clip.behavior_id !== 'string' || !clip.behavior_id.trim()) addValidationIssue(issues, 'error', '动作“' + label + '”缺少稳定 behavior_id。');

      // Catch actual non-finite values nested in imported parameters/frames,
      // including values not represented by the current inspector UI.
      collectNonFiniteNumbers(clip.params, '动作“' + label + '”参数', issues, new Set());
      collectNonFiniteNumbers(clip.keyframes, '动作“' + label + '”关键帧', issues, new Set());

      const frames = clip.keyframes;
      if (!Array.isArray(frames)) {
        addValidationIssue(issues, 'error', '动作“' + label + '”缺少关键帧数组。');
        return;
      }
      if (frames.length < 2) addValidationIssue(issues, 'error', '动作“' + label + '”至少需要两个关键帧。');

      const clipDuration = start != null && end != null ? end - start : null;
      let previousTime = null;
      frames.forEach((frame, frameIndex) => {
        if (!frame || typeof frame !== 'object') {
          addValidationIssue(issues, 'error', '动作“' + label + '”的关键帧 #' + (frameIndex + 1) + ' 数据格式无效。');
          return;
        }
        const frameTime = readFiniteValidationNumber(frame.t_s, '动作“' + label + '”关键帧 #' + (frameIndex + 1) + ' 时间', issues);
        if (frameTime != null) {
          if (frameTime < -.01 || (clipDuration != null && frameTime > clipDuration + .01)) {
            addValidationIssue(issues, 'error', '动作“' + label + '”的关键帧 #' + (frameIndex + 1) + ' 超出片段范围。');
          }
          if (previousTime != null && !(frameTime > previousTime)) {
            addValidationIssue(issues, 'error', '动作“' + label + '”的关键帧时间必须严格递增。');
          }
          previousTime = frameTime;
        }

        if (frame.position_cm && typeof frame.position_cm === 'object') {
          ['x', 'y', 'z'].forEach((axis) => {
            if (Object.prototype.hasOwnProperty.call(frame.position_cm, axis)) {
              readFiniteValidationNumber(frame.position_cm[axis], '动作“' + label + '”关键帧 #' + (frameIndex + 1) + ' 位置 ' + axis, issues);
            }
          });
        }
        if (frame.rotation_deg != null) readFiniteValidationNumber(frame.rotation_deg, '动作“' + label + '”关键帧 #' + (frameIndex + 1) + ' 旋转角度', issues);
        if (frame.scale != null) readFiniteValidationNumber(frame.scale, '动作“' + label + '”关键帧 #' + (frameIndex + 1) + ' 缩放值', issues);
        if (typeof frame.value === 'number') readFiniteValidationNumber(frame.value, '动作“' + label + '”关键帧 #' + (frameIndex + 1) + ' 值', issues);
      });
    });

    if (steps.filter(Boolean).some((step) => !clips.some((clip) => clip.step_id === step.id))) {
      addValidationIssue(issues, 'warning', '仍有说明块没有动作，导出时会保留其说明文本作为回退。');
    }
    steps.filter(Boolean).forEach((step) => {
      if (!Array.isArray(step.actions)) return;
      step.actions.forEach((action, actionIndex) => {
        const rawKind = action && (action.kind || action.action || action.type);
        if (!normalizeActionKind(rawKind)) addValidationIssue(issues, 'error', '说明块“' + (step.name || step.id) + '”的动作 #' + (actionIndex + 1) + '使用了未知动作类型。');
        const rawTarget = action && (action.target || action.target_ref);
        if (rawTarget && Array.isArray(step.targets) && step.targets.length && !step.targets.includes(rawTarget)) addValidationIssue(issues, 'warning', '说明块“' + (step.name || step.id) + '”的动作 #' + (actionIndex + 1) + '目标未列入 targets，已按动作目标保留。');
        const rawDuration = action && (action.duration_s != null ? action.duration_s : action.duration);
        if (rawDuration != null) {
          const durationValue = readFiniteValidationNumber(rawDuration, '说明块“' + (step.name || step.id) + '”动作 #' + (actionIndex + 1) + ' 时长', issues);
          if (durationValue != null && durationValue <= 0) addValidationIssue(issues, 'error', '说明块“' + (step.name || step.id) + '”动作 #' + (actionIndex + 1) + ' 时长必须大于 0。');
        }
        if (action && action.start_s != null) {
          const startValue = readFiniteValidationNumber(action.start_s, '说明块“' + (step.name || step.id) + '”动作 #' + (actionIndex + 1) + ' 开始时间', issues);
          if (startValue != null && startValue < 0) addValidationIssue(issues, 'error', '说明块“' + (step.name || step.id) + '”动作 #' + (actionIndex + 1) + ' 开始时间不能小于 0。');
        }
      });
    });
    if (clips.some((clip) => clip.generated && !clip.manual)) {
      addValidationIssue(issues, 'warning', '部分动作仍是自动生成草稿，导出前请确认轴向和时长。');
    }

    const stepIds = new Set(steps.map((step) => step && step.id).filter(Boolean));
    const dependencyGraph = new Map();
    steps.forEach((step) => {
      if (!step || !step.id) {
        addValidationIssue(issues, 'error', '存在缺少 ID 的说明块。');
        return;
      }
      const dependencies = Array.isArray(step.depends_on) ? step.depends_on : [];
      dependencies.forEach((dependency) => {
        if (!stepIds.has(dependency)) addValidationIssue(issues, 'error', '说明块“' + (step.name || step.id) + '”依赖了不存在的说明块。');
      });
      dependencyGraph.set(step.id, dependencies.filter((dependency) => stepIds.has(dependency)));
    });
    const visiting = new Set();
    const visited = new Set();
    const visitDependency = (id) => {
      if (visiting.has(id)) return true;
      if (visited.has(id)) return false;
      visiting.add(id);
      const cycle = (dependencyGraph.get(id) || []).some((dependency) => visitDependency(dependency));
      visiting.delete(id);
      visited.add(id);
      return cycle;
    };
    if (steps.filter((step) => step && step.id).some((step) => visitDependency(step.id))) addValidationIssue(issues, 'error', '说明块依赖关系存在循环。');

    const hasError = issues.some((issue) => issue.level === 'error');
    if (!hasError) issues.unshift({ level: 'ok', message: '结构、对象绑定、素材引用和关键帧检查通过。' });
    state.validation = { status: hasError ? 'blocked' : 'valid', issues: issues };
    validationFingerprint = buildValidationFingerprint();
    state.status = state.validation.status === 'valid' ? 'validated' : 'draft';
    renderExport();
    $('#footerMessage').textContent = state.validation.status === 'valid' ? '校验通过，可导出行为包' : '校验发现阻断项，请修复后再导出';
    toast(state.validation.status === 'valid' ? '校验完成：可以导出' : '校验完成：存在阻断项', state.validation.status === 'valid' ? 'ok' : 'err');
  }

  function updateClipField(clip, field, value) {
    if (field === 'loop') clip.loop = !!value;
    else if (field === 'start_s' || field === 'end_s') {
      const oldDuration = finiteOr(clip.end_s, 0) - finiteOr(clip.start_s, 0);
      clip[field] = value === '' ? NaN : Number(value);
      const newDuration = finiteOr(clip.end_s, 0) - finiteOr(clip.start_s, 0);
      if (Number.isFinite(oldDuration) && oldDuration > 0 && Number.isFinite(newDuration) && newDuration > 0) {
        (clip.keyframes || []).forEach((frame) => { frame.t_s = Number((finiteOr(frame.t_s, 0) / oldDuration * newDuration).toFixed(3)); });
      }
    }
    else clip[field] = value;
    clip.manual = true;
    clip.generated = false;
    if (!state.manualEdits.includes(clip.id)) state.manualEdits.push(clip.id);
  }

  function updateClipParam(clip, path, value) {
    const parts = path.split('.');
    if (parts.length === 2) {
      if (!clip.params[parts[0]]) clip.params[parts[0]] = {};
      clip.params[parts[0]][parts[1]] = parts[1] === 'x' || parts[1] === 'y' || parts[1] === 'z' ? Number(value) : value;
    } else {
      clip.params[path] = path === 'angle' ? Number(value) : value;
    }
    const frames = Array.isArray(clip.keyframes) ? clip.keyframes : [];
    if (frames.length < 2) {
      const duration = Math.max(.1, finiteOr(clip.end_s, 0) - finiteOr(clip.start_s, 0));
      clip.keyframes = makeKeyframes(clip.kind, clip.params, duration);
    } else if (clip.kind === 'move') {
      // Keep manually inserted middle frames; only the endpoints follow the
      // high-level from/to fields.
      frames[0].position_cm = clone(clip.params.from || { x: -120, y: 0, z: 0 });
      frames[frames.length - 1].position_cm = clone(clip.params.to || { x: 0, y: 0, z: 0 });
    } else if (clip.kind === 'rotate') {
      frames[0].rotation_deg = 0;
      frames[frames.length - 1].rotation_deg = Number(clip.params.angle);
    } else if (clip.kind === 'scale') {
      frames[0].scale = Number(clip.params.fromScale);
      frames[frames.length - 1].scale = Number(clip.params.toScale);
    }
    clip.manual = true;
    clip.generated = false;
    if (!state.manualEdits.includes(clip.id)) state.manualEdits.push(clip.id);
  }

  function updateObjectBinding(object, field, value) {
    if (!object || !['slot', 'asset_ref'].includes(field)) return false;
    const next = String(value == null ? '' : value).trim();
    if (object[field] === next) return false;
    object[field] = next;
    if (!objectBound(object)) object.capabilities = [];
    else if (!Array.isArray(object.capabilities) || !object.capabilities.length) object.capabilities = ['visibility', 'transform', 'material', 'fx', 'label'];
    invalidateValidation();
    state.dirty = true;
    updateSaveState();
    scheduleAutoSave();
    $('#footerMessage').textContent = '正在更新对象绑定';
    const status = $('#inspector-object .small-status');
    if (status) status.innerHTML = '<span class="status-dot ' + (objectBound(object) ? 'status-dot-ok' : 'status-dot-err') + '"></span>' + (objectBound(object) ? '已绑定' : '待绑定');
    return true;
  }

  function updateKeyframeField(frame, path, rawValue) {
    const parts = path.split('.');
    let target = frame;
    for (let index = 0; index < parts.length - 1; index += 1) {
      if (!target[parts[index]] || typeof target[parts[index]] !== 'object') target[parts[index]] = {};
      target = target[parts[index]];
    }
    const key = parts[parts.length - 1];
    const numeric = Number(rawValue);
    target[key] = rawValue === '' ? rawValue : (Number.isFinite(numeric) && (path !== 'value' || typeof target[key] === 'number') ? numeric : rawValue);
  }

  function addKeyframe() {
    const clip = selectedClip();
    if (!clip) return;
    pushHistory();
    const duration = Math.max(.1, clip.end_s - clip.start_s);
    const midpoint = Number((duration / 2).toFixed(2));
    const existing = clip.keyframes || [];
    if (existing.some((frame) => Math.abs(frame.t_s - midpoint) < .01)) {
      toast('中间位置已经存在关键帧', 'warn');
      return;
    }
    const first = existing[0] || { t_s: 0, value: 1 };
    const last = existing[existing.length - 1] || { t_s: duration, value: 1 };
    const frame = { t_s: midpoint };
    if (first.position_cm && last.position_cm) frame.position_cm = { x: (first.position_cm.x + last.position_cm.x) / 2, y: (first.position_cm.y + last.position_cm.y) / 2, z: (first.position_cm.z + last.position_cm.z) / 2 };
    else if (first.rotation_deg != null && last.rotation_deg != null) frame.rotation_deg = (first.rotation_deg + last.rotation_deg) / 2;
    else if (first.scale != null && last.scale != null) frame.scale = (first.scale + last.scale) / 2;
    else frame.value = .5;
    clip.keyframes.push(frame);
    clip.keyframes.sort((a, b) => a.t_s - b.t_s);
    clip.manual = true;
    clip.generated = false;
    markDirty('已添加中间关键帧');
    renderTimeline();
    renderClipInspector();
    applyPreview();
  }

  function deleteKeyframe(index) {
    const clip = selectedClip();
    if (!clip || clip.keyframes.length <= 2) return;
    pushHistory();
    clip.keyframes.splice(index, 1);
    clip.manual = true;
    clip.generated = false;
    markDirty('已删除关键帧');
    renderClipInspector();
    applyPreview();
  }

  function deleteClip() {
    const clip = selectedClip();
    if (!clip) return;
    openModal({
      title: '删除动作片段',
      body: '<p>删除“' + escapeHtml(clip.name) + '”后，时间轴中对应的动作将被移除。此操作可以用撤销恢复。</p>',
      actions: [
        { text: '取消', className: 'btn btn-ghost', close: true },
        { text: '删除动作', className: 'btn btn-primary', close: true, onClick: () => {
          pushHistory();
          state.tracks.forEach((track) => { track.clips = track.clips.filter((item) => item.id !== clip.id); });
          state.tracks = state.tracks.filter((track) => track.clips.length);
          state.selectedClipId = null;
          markDirty('已删除动作片段');
          renderAll();
        } }
      ]
    });
  }

  function addStep() {
    openModal({
      title: '添加说明块',
      body: '<div class="modal-body"><label class="form-row"><span class="label">名称</span><input id="modalStepName" class="field" placeholder="例如：安装防护罩"></label><label class="form-row"><span class="label">说明</span><textarea id="modalStepDescription" class="field" rows="3" placeholder="描述这一步要呈现的动作意图"></textarea></label></div>',
      actions: [
        { text: '取消', className: 'btn btn-ghost', close: true },
        { text: '添加', className: 'btn btn-primary', close: true, onClick: () => {
          const name = ($('#modalStepName') || {}).value || '';
          const description = ($('#modalStepDescription') || {}).value || '';
          if (!name.trim()) { toast('请填写说明块名称', 'warn'); return; }
          pushHistory();
          const index = state.spec.steps.length + 1;
          const step = { id: uid('step'), code: 'X' + String(index).padStart(2, '0'), name: name.trim(), category: '自定义', kind: 'sequence', description: description.trim(), standard: '用户补充', targets: ['assembly'] };
          state.spec.steps.push(step);
          state.selectedStepId = step.id;
          state.selectedObjectId = 'assembly';
          markDirty('已添加自定义说明块');
          renderAll();
        } }
      ]
    });
  }

  function newSpec() {
    const openNewSpecForm = () => openModal({
      title: '新建结构化动画说明',
      body: '<div class="modal-body"><label class="form-row"><span class="label">说明名称</span><input id="modalSpecName" class="field" value="新的动画说明"></label><label class="form-row"><span class="label">起始模板</span><select id="modalSpecTemplate" class="field">' + templates.map((template) => '<option value="' + template.id + '">' + escapeHtml(template.name) + '</option>').join('') + '</select></label><p class="panel-hint" style="margin:0">新建只会创建 Beta 本地草稿，不会写入 OntoTwin 项目。</p></div>',
      actions: [
        { text: '取消', className: 'btn btn-ghost', close: true },
        { text: '创建说明', className: 'btn btn-primary', close: true, onClick: () => {
          const name = ($('#modalSpecName') || {}).value || '新的动画说明';
          const templateId = ($('#modalSpecTemplate') || {}).value || 'template.assembly.v1';
           state = createInitialState(templateId);
           state.source.title = name.trim() || '新的动画说明';
           state.source.id = 'SPEC-LOCAL-' + String(getTemplate(templateId).generator || 'GENERIC').toUpperCase();
           state.source.origin = '用户新建的 Beta 草稿';
           state.source.revision = 'draft';
           state.spec.title = state.source.title;
           state.spec.id = state.source.id;
          state.package_id = packageIdFor(state.source.title);
          state.package_name = slugify(state.source.title);
          history = [];
          future = [];
          markDirty('已创建新的结构化动画说明');
          renderAll();
          setView('source');
          toast('已创建新的说明草稿', 'ok');
        } }
      ]
    });
    if (state.dirty || state.tracks.length) {
      openModal({
        title: '新建说明并替换当前草稿？',
        body: '<p>当前 Beta 草稿尚未完成保存或已有动画轨道。继续后会替换当前编辑内容，已保存草稿也不会自动合并。</p>',
        actions: [
          { text: '取消', className: 'btn btn-ghost', close: true },
          { text: '继续新建', className: 'btn btn-primary', close: true, onClick: () => window.setTimeout(openNewSpecForm, 0) }
        ]
      });
      return;
    }
    openNewSpecForm();
  }

  function addObject() {
    openModal({
      title: '添加受控对象',
      body: '<div class="modal-body"><label class="form-row"><span class="label">对象 ID</span><input id="modalObjectId" class="field" placeholder="例如 pump_body"></label><label class="form-row"><span class="label">对象名称</span><input id="modalObjectName" class="field" placeholder="例如 泵体"></label><label class="form-row"><span class="label">受控槽位</span><input id="modalObjectSlot" class="field" placeholder="例如 named:pump_body"></label><label class="form-row"><span class="label">逻辑资产</span><input id="modalObjectAsset" class="field" placeholder="例如 model.pump.body"></label><label class="form-row"><span class="label">3D mock 类型（可选）</span><input id="modalObjectMockAsset" class="field" placeholder="例如 pump-body / valve"></label><p class="panel-hint" style="margin:0">槽位或资产可以先留空，校验会提示需要补齐绑定；导出只保留 mock 识别标签，不导出几何。</p></div>',
      actions: [
        { text: '取消', className: 'btn btn-ghost', close: true },
        { text: '添加对象', className: 'btn btn-primary', close: true, onClick: () => {
          const id = String(($('#modalObjectId') || {}).value || '').trim();
           const name = String(($('#modalObjectName') || {}).value || id).trim();
           const slot = String(($('#modalObjectSlot') || {}).value || '').trim();
           const assetRef = String(($('#modalObjectAsset') || {}).value || '').trim();
           const mockAsset = String(($('#modalObjectMockAsset') || {}).value || '').trim();
           if (!id) { toast('请填写对象 ID', 'warn'); return; }
          if (state.objects.some((item) => item.id === id)) { toast('对象 ID 已存在', 'warn'); return; }
          pushHistory();
           state.objects.push(normalizeObjectRecord({ id: id, name: name || id, slot: slot, asset_ref: assetRef, mock_asset: mockAsset, capabilities: objectBound({ slot: slot, asset_ref: assetRef }) ? ['visibility', 'transform', 'material', 'fx', 'label'] : [] }));
          state.selectedObjectId = id;
          markDirty('已添加受控对象');
          renderAll();
        } }
      ]
    });
  }

  function openHelp() {
    openModal({
      title: 'PAE Beta 使用说明',
      body: '<div class="modal-body"><p><strong>1. 选择模板</strong><br>工序、装配和状态都是结构化动画说明的不同模板。</p><p><strong>2. 生成草稿</strong><br>“一键生成”只创建候选动作，请在时间轴中确认对象、轴向和时长。</p><p><strong>3. 导出行为包</strong><br>导出的 JSON 使用逻辑资产引用和稳定 behavior_id，供 A 角语义路由读取。</p><p><strong>4. 输入格式</strong><br>Beta 首期接受包含 <code>title</code>、<code>template_id</code>、<code>steps</code> 的结构化 JSON；不解析扫描件或自然语言。</p></div>',
      actions: [{ text: '知道了', className: 'btn btn-primary', close: true }]
    });
  }

  function openModal(options) {
    const root = $('#modalRoot');
    root.hidden = false;
    root.innerHTML = '<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle"><h3 id="modalTitle">' + escapeHtml(options.title || '请确认') + '</h3>' + (options.body || '') + '<div class="modal-foot">' + (options.actions || []).map((action, index) => '<button class="' + (action.className || 'btn') + '" data-modal-action="' + index + '">' + escapeHtml(action.text || '确定') + '</button>').join('') + '</div></div>';
    const close = () => { root.hidden = true; root.innerHTML = ''; };
    root.querySelector('.modal').addEventListener('click', (event) => {
      const button = event.target.closest('[data-modal-action]');
      if (!button) return;
      const action = options.actions[Number(button.dataset.modalAction)];
      if (action && action.onClick) action.onClick();
      if (!action || action.close !== false) close();
    });
    root.addEventListener('click', (event) => { if (event.target === root) close(); }, { once: true });
    const focusable = root.querySelector('input,select,textarea,button');
    if (focusable) window.setTimeout(() => focusable.focus(), 0);
    root._close = close;
  }

  function normalizeObjectRecord(raw, fallbackId) {
    const item = raw && typeof raw === 'object' ? raw : {};
    const id = String(item.id || item.ref || fallbackId || '').trim();
    if (!id) return null;
    const capabilities = Array.isArray(item.capabilities) ? item.capabilities.slice() : (typeof item.capabilities === 'string' ? item.capabilities.split(',').map((value) => value.trim()).filter(Boolean) : undefined);
    const record = {
      id: id,
      name: String(item.name || item.label || id),
      type: String(item.type || '待绑定对象'),
      slot: typeof item.slot === 'string' ? item.slot : '',
      asset_ref: typeof item.asset_ref === 'string' ? item.asset_ref : (typeof item.assetRef === 'string' ? item.assetRef : ''),
      mock_asset: typeof item.mock_asset === 'string' ? item.mock_asset : (typeof item.mockAsset === 'string' ? item.mockAsset : ''),
      description: String(item.description || '来自结构化说明的对象引用')
    };
    // Imported specifications may omit the optional capability list. A
    // bound object then receives the conservative generic primitive set;
    // explicitly supplied capabilities remain authoritative.
    record.capabilities = capabilities || (objectBound(record) ? ['visibility', 'transform', 'material', 'fx', 'label'] : []);
    return record;
  }

  function objectsForImport(data, steps) {
    const merged = clone(objects);
    const indexById = new Map(merged.map((item, index) => [item.id, index]));
    const imported = Array.isArray(data && data.objects) ? data.objects : [];
    imported.forEach((raw) => {
      const normalized = normalizeObjectRecord(raw);
      if (!normalized) return;
      if (indexById.has(normalized.id)) {
        const existing = merged[indexById.get(normalized.id)];
        const hasExplicitCapabilities = Array.isArray(raw && raw.capabilities) || typeof (raw && raw.capabilities) === 'string';
        const hasExplicitMockAsset = typeof (raw && raw.mock_asset) === 'string' || typeof (raw && raw.mockAsset) === 'string';
        merged[indexById.get(normalized.id)] = Object.assign({}, existing, normalized, hasExplicitCapabilities ? {} : { capabilities: existing.capabilities || normalized.capabilities }, hasExplicitMockAsset ? {} : { mock_asset: existing.mock_asset || normalized.mock_asset });
      }
      else { indexById.set(normalized.id, merged.length); merged.push(normalized); }
    });
    const targetIds = (steps || []).reduce((result, step) => {
      const stepTargets = Array.isArray(step && step.targets) ? step.targets : [];
      const actionTargets = Array.isArray(step && step.actions) ? step.actions.map((action) => action && (action.target || action.target_ref)).filter(Boolean) : [];
      return result.concat(stepTargets, actionTargets);
    }, []);
    targetIds.filter(Boolean).forEach((targetId) => {
      if (indexById.has(targetId)) return;
      indexById.set(targetId, merged.length);
      merged.push(normalizeObjectRecord({ id: targetId, name: targetId, type: '待绑定对象', mock_asset: 'generic-block', slot: '', asset_ref: '', capabilities: [] }));
    });
    return merged.filter(Boolean);
  }

  function handleImport(file) {
    const proceed = () => {
      const reader = new FileReader();
      reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        const importedSteps = data.steps || (data.spec && data.spec.steps) || data.blocks;
        if (!Array.isArray(importedSteps) || !importedSteps.length) throw new Error('缺少 steps/blocks');
        pushHistory();
        const requestedTemplateId = data.template_id || state.template_id;
        const template = findTemplate(requestedTemplateId);
        if (!template) throw new Error('未知模板');
        const title = String(data.title || data.name || (data.source && data.source.title) || state.source.title || template.defaultTitle).trim() || template.defaultTitle;
         const normalizedSteps = importedSteps.map((step, index) => {
           const actionTargets = Array.isArray(step && step.actions) ? step.actions.map((action) => action && (action.target || action.target_ref)).filter(Boolean) : [];
           const declaredTargets = Array.isArray(step && step.targets) ? step.targets.filter(Boolean) : [];
           const targets = declaredTargets.length ? declaredTargets : (actionTargets.length ? actionTargets : ['assembly']);
           return Object.assign({ id: uid('step'), code: 'X' + String(index + 1).padStart(2, '0'), name: '说明块 ' + (index + 1), category: '自定义', description: '', standard: '', targets: ['assembly'] }, step || {}, { id: (step && step.id) || uid('step'), name: String((step && step.name) || '说明块 ' + (index + 1)), targets: targets });
         });
        state.template_id = template.id;
        state.template_name = template.name;
        state.source = Object.assign({}, state.source, data.source || {}, { id: data.spec_id || (data.source && data.source.id) || state.source.id, title: title, origin: (data.source && data.source.origin) || '用户导入 JSON' });
        state.spec = { id: data.spec_id || state.source.id, title: title, template_id: template.id, meta: data.meta || {}, steps: normalizedSteps };
        state.objects = objectsForImport(data, normalizedSteps);
        state.package_id = data.package_id || packageIdFor(title);
        state.package_name = data.package_name || slugify(title);
        state.tracks = [];
        state.duration_s = 12;
        state.export_range = 'all';
        state.export_format = 'behavior-package-v1';
        state.manualEdits = [];
        state.selectedStepId = state.spec.steps[0].id;
        state.selectedObjectId = state.spec.steps[0].targets[0] || 'assembly';
        state.selectedClipId = null;
        state.stage_offset = { x: 0, y: 0 };
        state.validation = null;
        markDirty('已导入结构化动画说明，请确认字段映射');
        renderAll();
        setView('source');
        toast('已导入 ' + state.spec.steps.length + ' 个说明块', 'ok');
      } catch (error) {
        toast('导入失败：需要包含 steps 或 blocks 数组的 JSON', 'err');
      }
      };
      reader.readAsText(file, 'utf-8');
    };
    if (state.dirty || state.tracks.length) {
      openModal({
        title: '导入说明并替换当前草稿？',
        body: '<p>当前 Beta 草稿尚未完成保存或已有动画轨道。导入后会替换当前编辑内容，继续前请确认不需要合并。</p>',
        actions: [
          { text: '取消', className: 'btn btn-ghost', close: true },
          { text: '继续导入', className: 'btn btn-primary', close: true, onClick: () => window.setTimeout(proceed, 0) }
        ]
      });
      return;
    }
    proceed();
  }

  function downloadManifest() {
    if (!state.validation || state.validation.status !== 'valid' || !validationIsCurrent()) {
      toast('内容已变化或尚未校验，请重新运行校验后再导出', 'warn');
      return;
    }
    const payload = state.export_format === 'storyboard-json' ? buildStoryboardPayload() : buildManifest();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = slugify(state.package_name || 'behavior-package') + '.json';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('行为包已下载', 'ok');
  }

  function copyManifest() {
    const content = $('#manifestPreview').textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => toast('Manifest JSON 已复制', 'ok')).catch(() => toast('复制失败，请手动选择文本', 'warn'));
    } else {
      toast('当前浏览器不支持自动复制，请手动选择文本', 'warn');
    }
  }

  function copyARouteSample() {
    const sample = buildARouteSample();
    if (!sample) {
      toast('请先生成至少一个动作片段', 'warn');
      return;
    }
    const content = JSON.stringify(sample, null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => toast('A 角调用样例已复制', 'ok')).catch(() => toast('复制失败，请手动选择文本', 'warn'));
    } else {
      toast('当前浏览器不支持自动复制，请手动选择文本', 'warn');
    }
  }

  function togglePlay() {
    if (playing) stopPlayback();
    else startPlayback();
  }

  function startPlayback() {
    playing = true;
    $('#playBtn').textContent = '暂停';
    $('#playBtn').setAttribute('aria-label', '暂停');
    $('#previewStatus').textContent = '正在预览';
    lastFrame = performance.now();
    rafId = requestAnimationFrame(playFrame);
  }

  function stopPlayback() {
    playing = false;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
    $('#playBtn').textContent = '播放';
    $('#playBtn').setAttribute('aria-label', '播放');
    $('#previewStatus').textContent = '预览就绪';
  }

  function playFrame(timestamp) {
    if (!playing) return;
    const elapsed = (timestamp - lastFrame) / 1000 * Number($('#speedSelect').value || 1);
    lastFrame = timestamp;
    state.playhead_s += elapsed;
    if (state.playhead_s >= state.duration_s) {
      if ($('#loopToggle').checked) state.playhead_s = 0;
      else { state.playhead_s = state.duration_s; stopPlayback(); }
    }
    renderTimeline();
    applyPreview();
    if (playing) rafId = requestAnimationFrame(playFrame);
  }

  function timeFromTimelinePointer(event) {
    const viewport = $('#timelineViewport');
    const rect = viewport.getBoundingClientRect();
    const x = clamp(event.clientX - rect.left + viewport.scrollLeft, 0, viewport.scrollWidth);
    const ratio = viewport.scrollWidth ? x / viewport.scrollWidth : 0;
    return clamp(ratio * state.duration_s, 0, state.duration_s);
  }

  function setPlayheadFromPointer(event) {
    state.playhead_s = timeFromTimelinePointer(event);
    renderTimeline();
    applyPreview();
  }

  function easingValue(progress, easing) {
    const t = clamp(progress, 0, 1);
    if (easing === 'linear') return t;
    if (easing === 'ease-in') return t * t;
    return t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  function interpolateFrames(clip, localTime) {
    const frames = (clip.keyframes || []).slice().sort((a, b) => a.t_s - b.t_s);
    if (!frames.length) return {};
    if (localTime <= frames[0].t_s) return frames[0];
    if (localTime >= frames[frames.length - 1].t_s) return frames[frames.length - 1];
    let left = frames[0];
    let right = frames[frames.length - 1];
    for (let index = 1; index < frames.length; index += 1) {
      if (localTime <= frames[index].t_s) { right = frames[index]; left = frames[index - 1]; break; }
    }
    const ratio = easingValue((localTime - left.t_s) / Math.max(.0001, right.t_s - left.t_s), clip.easing);
    const output = { t_s: localTime };
    if (left.position_cm && right.position_cm) output.position_cm = { x: left.position_cm.x + (right.position_cm.x - left.position_cm.x) * ratio, y: left.position_cm.y + (right.position_cm.y - left.position_cm.y) * ratio, z: left.position_cm.z + (right.position_cm.z - left.position_cm.z) * ratio };
    if (left.rotation_deg != null && right.rotation_deg != null) output.rotation_deg = left.rotation_deg + (right.rotation_deg - left.rotation_deg) * ratio;
    if (left.scale != null && right.scale != null) output.scale = left.scale + (right.scale - left.scale) * ratio;
    if (left.value != null && right.value != null) output.value = left.value + (right.value - left.value) * ratio;
    return output;
  }

  function svgObjectForTarget(svg, targetId) {
    return $$('.svg-object', svg).find((element) => element.dataset.target === targetId) || null;
  }

  // -------------------------------------------------------------------------
  // Dependency-free 3D mock renderer
  // -------------------------------------------------------------------------
  // The renderer intentionally stays local to the Beta workbench.  These are
  // real triangle meshes (boxes, cylinders, toruses and spheres), not flat
  // icons.  They stand in for logical asset_ref values until a project-owned
  // asset adapter is supplied by the UE execution role.

  function cssToken(name, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name);
    return value && value.trim() ? value.trim() : fallback;
  }

  function parseColor3d(value) {
    const text = String(value || '').trim();
    let match = text.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
    if (match) {
      const raw = match[1].length === 3 ? match[1].split('').map((part) => part + part).join('') : match[1];
      return { r: parseInt(raw.slice(0, 2), 16), g: parseInt(raw.slice(2, 4), 16), b: parseInt(raw.slice(4, 6), 16) };
    }
    match = text.match(/^rgba?\(\s*([\d.]+)[, ]+\s*([\d.]+)[, ]+\s*([\d.]+)/i);
    if (match) return { r: Number(match[1]), g: Number(match[2]), b: Number(match[3]) };
    return null;
  }

  function rgba3d(value, alpha) {
    const rgb = parseColor3d(value);
    return rgb ? 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',' + clamp(alpha, 0, 1) + ')' : value;
  }

  function shade3d(value, amount) {
    const rgb = parseColor3d(value);
    if (!rgb) return value;
    const factor = amount >= 0 ? 255 * amount : 255 * amount;
    return 'rgb(' + clamp(Math.round(rgb.r + factor), 0, 255) + ',' + clamp(Math.round(rgb.g + factor), 0, 255) + ',' + clamp(Math.round(rgb.b + factor), 0, 255) + ')';
  }

  function v3(x, y, z) { return { x: Number(x) || 0, y: Number(y) || 0, z: Number(z) || 0 }; }
  function v3Add(a, b) { return v3(a.x + b.x, a.y + b.y, a.z + b.z); }
  function v3Sub(a, b) { return v3(a.x - b.x, a.y - b.y, a.z - b.z); }
  function v3Scale(a, amount) { return v3(a.x * amount, a.y * amount, a.z * amount); }
  function v3Dot(a, b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
  function v3Cross(a, b) { return v3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x); }
  function v3Length(a) { return Math.sqrt(v3Dot(a, a)); }
  function v3Normalize(a) { const length = v3Length(a) || 1; return v3Scale(a, 1 / length); }

  function rotateEuler3d(point, rotation) {
    const r = rotation || {};
    const sx = Math.sin(Number(r.x) || 0); const cx = Math.cos(Number(r.x) || 0);
    const sy = Math.sin(Number(r.y) || 0); const cy = Math.cos(Number(r.y) || 0);
    const sz = Math.sin(Number(r.z) || 0); const cz = Math.cos(Number(r.z) || 0);
    let output = v3(point.x, point.y * cx - point.z * sx, point.y * sx + point.z * cx);
    output = v3(output.x * cy + output.z * sy, output.y, -output.x * sy + output.z * cy);
    output = v3(output.x * cz - output.y * sz, output.x * sz + output.y * cz, output.z);
    return output;
  }

  function rotateAxis3d(point, angleDeg, axis) {
    const radians = (Number(angleDeg) || 0) * Math.PI / 180;
    const sin = Math.sin(radians); const cos = Math.cos(radians);
    const axisName = String(axis || 'Z').toUpperCase();
    if (axisName === 'X') return v3(point.x, point.y * cos - point.z * sin, point.y * sin + point.z * cos);
    if (axisName === 'Y') return v3(point.x * cos + point.z * sin, point.y, -point.x * sin + point.z * cos);
    return v3(point.x * cos - point.y * sin, point.x * sin + point.y * cos, point.z);
  }

  function meshBox3d(width, depth, height) {
    const w = width / 2; const d = depth / 2; const h = height / 2;
    return {
      vertices: [v3(-w, -d, -h), v3(w, -d, -h), v3(w, d, -h), v3(-w, d, -h), v3(-w, -d, h), v3(w, -d, h), v3(w, d, h), v3(-w, d, h)],
      faces: [
        { indices: [0, 3, 2, 1], material: 'dark' },
        { indices: [4, 5, 6, 7], material: 'top' },
        { indices: [0, 1, 5, 4], material: 'surface' },
        { indices: [1, 2, 6, 5], material: 'side' },
        { indices: [2, 3, 7, 6], material: 'side' },
        { indices: [3, 0, 4, 7], material: 'surface' }
      ]
    };
  }

  function meshCylinder3d(radius, height, segments) {
    const count = Math.max(8, Math.floor(segments || 16));
    const vertices = [];
    for (let index = 0; index < count; index += 1) {
      const angle = index / count * Math.PI * 2;
      vertices.push(v3(Math.cos(angle) * radius, Math.sin(angle) * radius, -height / 2));
    }
    for (let index = 0; index < count; index += 1) {
      const angle = index / count * Math.PI * 2;
      vertices.push(v3(Math.cos(angle) * radius, Math.sin(angle) * radius, height / 2));
    }
    const faces = [{ indices: Array.from({ length: count }, (_, index) => count - 1 - index), material: 'dark' }, { indices: Array.from({ length: count }, (_, index) => count + index), material: 'top' }];
    for (let index = 0; index < count; index += 1) {
      const next = (index + 1) % count;
      faces.push({ indices: [index, next, count + next, count + index], material: index % 3 === 0 ? 'side' : 'surface' });
    }
    return { vertices: vertices, faces: faces };
  }

  function meshTorus3d(majorRadius, minorRadius, majorSegments, minorSegments) {
    const major = Math.max(12, Math.floor(majorSegments || 24));
    const minor = Math.max(6, Math.floor(minorSegments || 8));
    const vertices = [];
    for (let majorIndex = 0; majorIndex < major; majorIndex += 1) {
      const majorAngle = majorIndex / major * Math.PI * 2;
      for (let minorIndex = 0; minorIndex < minor; minorIndex += 1) {
        const minorAngle = minorIndex / minor * Math.PI * 2;
        const ring = majorRadius + minorRadius * Math.cos(minorAngle);
        vertices.push(v3(ring * Math.cos(majorAngle), ring * Math.sin(majorAngle), minorRadius * Math.sin(minorAngle)));
      }
    }
    const faces = [];
    for (let majorIndex = 0; majorIndex < major; majorIndex += 1) {
      const nextMajor = (majorIndex + 1) % major;
      for (let minorIndex = 0; minorIndex < minor; minorIndex += 1) {
        const nextMinor = (minorIndex + 1) % minor;
        faces.push({ indices: [majorIndex * minor + minorIndex, nextMajor * minor + minorIndex, nextMajor * minor + nextMinor, majorIndex * minor + nextMinor], material: minorIndex % 3 === 0 ? 'top' : 'surface' });
      }
    }
    return { vertices: vertices, faces: faces };
  }

  function meshSphere3d(radius, rings, segments) {
    const ringCount = Math.max(6, Math.floor(rings || 10));
    const segmentCount = Math.max(12, Math.floor(segments || 20));
    const vertices = [];
    for (let ring = 0; ring <= ringCount; ring += 1) {
      const phi = ring / ringCount * Math.PI;
      for (let segment = 0; segment < segmentCount; segment += 1) {
        const theta = segment / segmentCount * Math.PI * 2;
        vertices.push(v3(radius * Math.sin(phi) * Math.cos(theta), radius * Math.sin(phi) * Math.sin(theta), radius * Math.cos(phi)));
      }
    }
    const faces = [];
    for (let ring = 0; ring < ringCount; ring += 1) {
      for (let segment = 0; segment < segmentCount; segment += 1) {
        const next = (segment + 1) % segmentCount;
        const row = ring * segmentCount; const nextRow = (ring + 1) * segmentCount;
        faces.push({ indices: [row + segment, nextRow + segment, nextRow + next, row + next], material: 'indicator' });
      }
    }
    return { vertices: vertices, faces: faces };
  }

  function part3d(mesh, position, rotation, scale, material) {
    return { mesh: mesh, position: position || v3(0, 0, 0), rotation: rotation || { x: 0, y: 0, z: 0 }, scale: scale || v3(1, 1, 1), material: material || 'surface' };
  }

  function cachedMesh3d(key, factory) {
    if (!meshCache3d.has(key)) meshCache3d.set(key, factory());
    return meshCache3d.get(key);
  }

  function assetKind3d(object) {
    const value = ((object && object.id) || '') + ' ' + ((object && object.asset_ref) || '') + ' ' + ((object && object.mock_asset) || '') + ' ' + ((object && object.type) || '') + ' ' + ((object && object.name) || '');
    const haystack = value.toLowerCase();
    if ((object && object.id === 'label') || haystack.includes('label') || haystack.includes('字幕') || haystack.includes('text')) return 'label';
    if (haystack.includes('bearing') || haystack.includes('轴承')) return 'bearing';
    if (haystack.includes('indicator') || haystack.includes('light') || haystack.includes('指示') || haystack.includes('灯')) return 'indicator';
    if (haystack.includes('pump') || haystack.includes('泵')) return 'pump';
    if (haystack.includes('valve') || haystack.includes('阀')) return 'valve';
    if (haystack.includes('tool') || haystack.includes('fixture') || haystack.includes('工具')) return 'tool';
    if (haystack.includes('rod') || haystack.includes('link') || haystack.includes('连杆')) return 'rod';
    if ((object && object.id === 'assembly') || haystack.includes('assembly') || haystack.includes('base') || haystack.includes('基座')) return 'base';
    return 'generic';
  }

  function assetPose3d(object, index) {
    const id = object && object.id;
    if (id === 'assembly') return { position: v3(0, 0, 22), radius: 290, label: v3(0, 0, 92) };
    if (id === 'rod') return { position: v3(0, 0, 102), radius: 190, label: v3(0, 0, 145) };
    if (id === 'bearing-left') return { position: v3(-145, 0, 112), radius: 65, label: v3(-145, 0, 180) };
    if (id === 'bearing-right') return { position: v3(145, 0, 112), radius: 65, label: v3(145, 0, 180) };
    if (id === 'tool') return { position: v3(0, 0, 245), radius: 85, label: v3(0, 0, 330) };
    if (id === 'label') return { position: v3(0, -100, 265), radius: 120, label: v3(0, -100, 285) };
    if (id === 'pump_body') return { position: v3(-50, 0, 96), radius: 120, label: v3(-50, 0, 220) };
    if (id === 'pump_indicator') return { position: v3(105, -4, 205), radius: 32, label: v3(105, -4, 250) };
    const column = index % 3; const row = Math.floor(index / 3);
    return { position: v3(-210 + column * 210, 100 + row * 110, 70), radius: 75, label: v3(-210 + column * 210, 100 + row * 110, 145) };
  }

  function assetDefinition3d(object) {
    const kind = assetKind3d(object);
    const paletteKey = kind + ':' + ((object && object.id) || '');
    if (meshCache3d.has(paletteKey)) return meshCache3d.get(paletteKey);
    const box = (width, depth, height) => cachedMesh3d('box:' + width + ':' + depth + ':' + height, () => meshBox3d(width, depth, height));
    const cylinder = (radius, height, segments) => cachedMesh3d('cylinder:' + radius + ':' + height + ':' + segments, () => meshCylinder3d(radius, height, segments));
    const torus = (major, minor) => cachedMesh3d('torus:' + major + ':' + minor, () => meshTorus3d(major, minor, 24, 8));
    const sphere = (radius) => cachedMesh3d('sphere:' + radius, () => meshSphere3d(radius, 9, 18));
    let definition;
    if (kind === 'base') {
      definition = { kind: kind, radius: 290, parts: [part3d(box(460, 235, 38), v3(0, 0, 0), null, null, 'base'), part3d(box(390, 175, 12), v3(0, 0, 29), null, null, 'top'), part3d(cylinder(14, 12, 16), v3(-185, -83, 31), null, null, 'metal'), part3d(cylinder(14, 12, 16), v3(185, -83, 31), null, null, 'metal')] };
    } else if (kind === 'rod') {
      definition = { kind: kind, radius: 190, parts: [part3d(box(285, 58, 34), v3(0, 0, 0), null, null, 'metal'), part3d(cylinder(43, 28, 20), v3(-126, 0, 24), null, null, 'light'), part3d(cylinder(43, 28, 20), v3(126, 0, 24), null, null, 'light'), part3d(box(120, 28, 18), v3(0, 0, 28), null, null, 'accent')] };
    } else if (kind === 'bearing') {
      definition = { kind: kind, radius: 67, parts: [part3d(cylinder(51, 28, 24), v3(0, 0, 0), null, null, 'metal'), part3d(torus(34, 8), v3(0, 0, 17), null, null, 'accent'), part3d(cylinder(23, 34, 24), v3(0, 0, 8), null, null, 'light'), part3d(cylinder(12, 37, 20), v3(0, 0, 12), null, null, 'dark')] };
    } else if (kind === 'tool') {
      definition = { kind: kind, radius: 88, parts: [part3d(box(70, 70, 115), v3(0, 0, 5), null, null, 'dark'), part3d(box(110, 84, 24), v3(0, 0, 66), null, null, 'metal'), part3d(cylinder(16, 55, 16), v3(0, 0, -72), null, null, 'accent')] };
    } else if (kind === 'label') {
      definition = { kind: kind, radius: 125, parts: [part3d(box(220, 18, 50), v3(0, 0, 0), null, null, 'light'), part3d(box(190, 5, 35), v3(0, -12, 0), null, null, 'accent')] };
    } else if (kind === 'pump') {
      definition = { kind: kind, radius: 130, parts: [part3d(cylinder(76, 118, 28), v3(0, 0, 0), null, null, 'base'), part3d(box(128, 105, 44), v3(0, 0, -54), null, null, 'metal'), part3d(cylinder(30, 36, 20), v3(70, 0, 0), { x: 0, y: Math.PI / 2, z: 0 }, null, 'accent'), part3d(box(24, 78, 68), v3(-78, 0, 23), null, null, 'top')] };
    } else if (kind === 'indicator') {
      definition = { kind: kind, radius: 34, parts: [part3d(cylinder(22, 10, 20), v3(0, 0, -6), null, null, 'dark'), part3d(sphere(25), v3(0, 0, 16), null, null, 'indicator')] };
    } else if (kind === 'valve') {
      definition = { kind: kind, radius: 92, parts: [part3d(cylinder(42, 35, 20), v3(0, 0, 0), null, null, 'metal'), part3d(box(105, 32, 18), v3(0, 0, 38), null, null, 'accent'), part3d(cylinder(12, 86, 16), v3(0, 0, 80), null, null, 'dark')] };
    } else {
      definition = { kind: kind, radius: 78, parts: [part3d(box(108, 82, 74), v3(0, 0, 0), null, null, 'surface'), part3d(cylinder(16, 20, 16), v3(-36, -26, 45), null, null, 'accent')] };
    }
    meshCache3d.set(paletteKey, definition);
    return definition;
  }

  function palette3d() {
    return {
      ink: cssToken('--ink', '#1a1a1a'),
      ink2: cssToken('--ink-2', '#5c5c5c'),
      ink3: cssToken('--ink-3', '#8a8a8a'),
      line: cssToken('--line', '#e8e8e8'),
      line2: cssToken('--line-2', '#d4d4d4'),
      bg: cssToken('--bg', '#ffffff'),
      bg2: cssToken('--bg-2', '#fafafa'),
      bg3: cssToken('--bg-3', '#f3f3f3'),
      ok: cssToken('--ok', '#067647'),
      warn: cssToken('--warn', '#b54708'),
      danger: cssToken('--danger', '#b42318'),
      info: cssToken('--info', '#363f72')
    };
  }

  function materialColor3d(material, visual, palette) {
    if (visual && visual.flash) return palette.warn;
    if (visual && visual.material) {
      const value = String(visual.materialValue || '').toLowerCase();
      if (value.includes('warning') || value.includes('alarm') || value.includes('fault') || value.includes('告警')) return palette.danger;
      if (value.includes('running') || value.includes('ok') || value.includes('运行')) return palette.ok;
      return palette.info;
    }
    if (material === 'dark') return palette.ink;
    if (material === 'top') return palette.bg;
    if (material === 'light') return palette.bg2;
    if (material === 'accent') return palette.info;
    if (material === 'indicator') return palette.ok;
    if (material === 'metal') return palette.ink2;
    if (material === 'base') return palette.line2;
    return palette.ink3;
  }

  function cameraBasis3d(width, height) {
    const pitch = clamp(camera3d.pitch, -1.25, 1.25);
    const distance = clamp(camera3d.distance, 260, 2200);
    const target = v3(camera3d.target.x, camera3d.target.y, camera3d.target.z);
    const cameraPosition = v3(target.x + distance * Math.cos(pitch) * Math.sin(camera3d.yaw), target.y + distance * Math.cos(pitch) * Math.cos(camera3d.yaw), target.z + distance * Math.sin(pitch));
    const forward = v3Normalize(v3Sub(target, cameraPosition));
    const worldUp = v3(0, 0, 1);
    let right = v3Normalize(v3Cross(worldUp, forward));
    if (v3Length(right) < .001) right = v3(1, 0, 0);
    const up = v3Normalize(v3Cross(forward, right));
    return { position: cameraPosition, forward: forward, right: right, up: up, focal: Math.min(width, height) * 1.15, width: width, height: height };
  }

  function project3d(point, basis) {
    const relative = v3Sub(point, basis.position);
    const depth = v3Dot(relative, basis.forward);
    if (depth <= 1) return null;
    const scale = basis.focal / depth;
    return { x: basis.width / 2 + camera3d.panX + v3Dot(relative, basis.right) * scale, y: basis.height / 2 + camera3d.panY - v3Dot(relative, basis.up) * scale, depth: depth };
  }

  function transformAssetPoint3d(point, part, pose, visual) {
    const local = v3(point.x * (part.scale.x || 1), point.y * (part.scale.y || 1), point.z * (part.scale.z || 1));
    const rotatedPart = rotateEuler3d(local, part.rotation);
    const partPoint = v3Add(rotatedPart, part.position);
    const objectScale = Math.max(.01, finiteOr(visual && visual.scale, 1));
    const scaled = v3Scale(partPoint, objectScale);
    const objectRotation = rotateAxis3d(scaled, visual && visual.rotation, visual && visual.rotationAxis);
    return v3Add(v3Add(objectRotation, pose.position), v3(finiteOr(visual && visual.x, 0), finiteOr(visual && visual.y, 0), finiteOr(visual && visual.z, 0)));
  }

  function resize3dCanvas() {
    const canvas = $('#preview3d');
    if (!canvas) return false;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(320, Math.floor(rect.width || canvas.clientWidth || 640));
    const height = Math.max(240, Math.floor(rect.height || canvas.clientHeight || 360));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
    }
    renderer3d.canvas = canvas;
    renderer3d.ctx = canvas.getContext('2d');
    const viewport = $('#stageViewport');
    const fallbackSvg = $('#previewSvg');
    if (!renderer3d.ctx) {
      if (viewport) viewport.classList.add('svg-fallback');
      if (fallbackSvg) fallbackSvg.hidden = false;
      return false;
    }
    if (viewport) viewport.classList.remove('svg-fallback');
    if (fallbackSvg) fallbackSvg.hidden = true;
    renderer3d.width = width;
    renderer3d.height = height;
    renderer3d.dpr = dpr;
    if (renderer3d.ctx) renderer3d.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return !!renderer3d.ctx;
  }

  function drawLine3d(ctx, from, to, stroke, width, alpha) {
    if (!from || !to) return;
    ctx.save();
    ctx.globalAlpha = alpha == null ? 1 : alpha;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = width || 1;
    ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(to.x, to.y); ctx.stroke();
    ctx.restore();
  }

  function renderGround3d(ctx, basis, palette) {
    if (!state.grid) return;
    for (let value = -520; value <= 520; value += 50) {
      drawLine3d(ctx, project3d(v3(value, -520, 0), basis), project3d(v3(value, 520, 0), basis), palette.ink3, value % 250 === 0 ? 1 : .6, value % 250 === 0 ? .25 : .12);
      drawLine3d(ctx, project3d(v3(-520, value, 0), basis), project3d(v3(520, value, 0), basis), palette.ink3, value % 250 === 0 ? 1 : .6, value % 250 === 0 ? .25 : .12);
    }
    drawLine3d(ctx, project3d(v3(-580, 0, 0), basis), project3d(v3(580, 0, 0), basis), palette.info, 1.4, .58);
    drawLine3d(ctx, project3d(v3(0, -580, 0), basis), project3d(v3(0, 580, 0), basis), palette.warn, 1.4, .42);
  }

  function render3DScene(visuals) {
    if (!resize3dCanvas()) return;
    const ctx = renderer3d.ctx;
    const width = renderer3d.width; const height = renderer3d.height;
    const palette = palette3d();
    const basis = cameraBasis3d(width, height);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = palette.bg2;
    ctx.fillRect(0, 0, width, height);
    renderGround3d(ctx, basis, palette);
    const faces = [];
    const labels = [];
    const projectedObjects = [];
    const objectList = Array.isArray(state.objects) ? state.objects : [];
    objectList.forEach((object, index) => {
      if (!object || !object.id) return;
      const visual = visuals.get(object.id) || { opacity: 1, x: 0, y: 0, z: 0, rotation: 0, rotationAxis: 'Z', scale: 1, flash: false, material: false, materialValue: '' };
      const pose = assetPose3d(object, index);
      const definition = assetDefinition3d(object);
      const objectOpacity = clamp(finiteOr(visual.opacity, 1), 0, 1);
      const center = v3Add(pose.position, v3(finiteOr(visual.x, 0), finiteOr(visual.y, 0), finiteOr(visual.z, 0)));
      const projectedCenter = project3d(center, basis);
      if (projectedCenter) {
        const edge = project3d(v3Add(center, v3(definition.radius * Math.max(.01, finiteOr(visual.scale, 1)), 0, 0)), basis);
        projectedObjects.push({ id: object.id, x: projectedCenter.x, y: projectedCenter.y, radius: edge ? Math.max(18, Math.abs(edge.x - projectedCenter.x)) : 28, depth: projectedCenter.depth });
      }
      definition.parts.forEach((part) => {
        const transformed = part.mesh.vertices.map((vertex) => transformAssetPoint3d(vertex, part, pose, visual));
        part.mesh.faces.forEach((face) => {
          const points = face.indices.map((vertexIndex) => transformed[vertexIndex]);
          const projected = points.map((point) => project3d(point, basis));
          if (projected.some((point) => !point)) return;
          const normal = points.length >= 3 ? v3Normalize(v3Cross(v3Sub(points[1], points[0]), v3Sub(points[2], points[0]))) : v3(0, 0, 1);
          const centerPoint = points.reduce((sum, point) => v3Add(sum, point), v3(0, 0, 0));
          const centerAverage = v3Scale(centerPoint, 1 / points.length);
          const projectedAverage = project3d(centerAverage, basis);
          if (!projectedAverage) return;
          const depth = projectedAverage.depth;
          faces.push({ points: projected, depth: depth, color: materialColor3d(part.material || face.material, visual, palette), opacity: objectOpacity, normal: normal, selected: object.id === state.selectedObjectId });
        });
      });
      const labelPoint = project3d(v3Add(center, v3(0, 0, definition.kind === 'label' ? 0 : 38)), basis);
      // Keep the viewport readable when an imported spec contains many
      // objects. The object tree remains the complete legend; the 3D view
      // labels the picked object and annotation panel, plus all objects in a
      // small scene.
      if (labelPoint && (object.id === state.selectedObjectId || definition.kind === 'label' || objectList.length <= 5)) labels.push({ object: object, point: labelPoint, selected: object.id === state.selectedObjectId, text: visual.labelValue || objectName(object, object.id) });
      if (visual.flash && projectedCenter) {
        ctx.save(); ctx.globalAlpha = .2 * objectOpacity; ctx.fillStyle = palette.warn; ctx.beginPath(); ctx.arc(projectedCenter.x, projectedCenter.y, projectedObjects[projectedObjects.length - 1].radius * 1.35, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      }
    });
    faces.sort((left, right) => right.depth - left.depth);
    faces.forEach((face) => {
      const light = Math.max(0, v3Dot(face.normal, v3Normalize(v3(-.45, -.65, 1))));
      const fill = shade3d(face.color, -.16 + light * .34);
      ctx.save(); ctx.globalAlpha = face.opacity; ctx.fillStyle = fill; ctx.strokeStyle = rgba3d(palette.ink, face.selected ? .5 : .16); ctx.lineWidth = face.selected ? 1.2 : .55;
      ctx.beginPath(); face.points.forEach((point, index) => { if (index === 0) ctx.moveTo(point.x, point.y); else ctx.lineTo(point.x, point.y); }); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
    });
    labels.sort((left, right) => right.point.depth - left.point.depth);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    labels.forEach((entry) => {
       const label = String(entry.text || objectName(entry.object, entry.object.id)).slice(0, 24);
      ctx.save(); ctx.font = (entry.selected ? '600 ' : '500 ') + '11px ' + cssToken('--font', 'sans-serif'); ctx.fillStyle = entry.selected ? palette.ink : palette.ink2; ctx.globalAlpha = entry.selected ? 1 : .74;
      const textWidth = ctx.measureText(label).width + 12;
      ctx.fillStyle = rgba3d(palette.bg, .82); ctx.fillRect(entry.point.x - textWidth / 2, entry.point.y - 9, textWidth, 18);
      ctx.fillStyle = entry.selected ? palette.ink : palette.ink2; ctx.fillText(label, entry.point.x, entry.point.y); ctx.restore();
    });
    const selected = projectedObjects.find((item) => item.id === state.selectedObjectId);
    if (selected) {
      ctx.save(); ctx.strokeStyle = palette.info; ctx.lineWidth = 2; ctx.setLineDash([5, 4]); ctx.globalAlpha = .9; ctx.beginPath(); ctx.arc(selected.x, selected.y, selected.radius + 8, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    }
    ctx.save(); ctx.font = '600 10px ' + cssToken('--font', 'sans-serif'); ctx.fillStyle = palette.ink3; ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillText('MOCK 3D ASSET  ·  ' + objectList.length + ' 对象', 12, 12); ctx.textAlign = 'right'; ctx.fillText('视角 ' + Math.round(camera3d.yaw * 180 / Math.PI) + '°  /  ' + Math.round(camera3d.pitch * 180 / Math.PI) + '°', width - 12, 12); ctx.restore();
    renderer3d.projectedObjects = projectedObjects;
    const cameraReadout = $('#stageCameraReadout');
    if (cameraReadout) cameraReadout.textContent = '视角 ' + Math.round(camera3d.yaw * 180 / Math.PI) + '° · 缩放 ' + Math.round(760 / camera3d.distance * 100) + '%';
  }

  function pick3dObject(clientX, clientY) {
    const canvas = renderer3d.canvas;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left; const y = clientY - rect.top;
    const candidates = renderer3d.projectedObjects.filter((item) => Math.hypot(item.x - x, item.y - y) <= item.radius + 10).sort((a, b) => (a.depth - b.depth) || (Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y)));
    return candidates.length ? candidates[0].id : null;
  }

  function frameAtAbsoluteTime(clip, absoluteTime) {
    const start = finiteOr(clip.start_s, 0);
    const end = finiteOr(clip.end_s, start + 1);
    return interpolateFrames(clip, clamp(absoluteTime - start, 0, Math.max(.001, end - start)));
  }

  function svgPivot(targetId) {
    return ({ assembly: '450 238', rod: '450 238', 'bearing-left': '310 238', 'bearing-right': '590 238', tool: '450 120', label: '450 367' })[targetId] || '450 238';
  }

  function syncDynamicSvgObjects() {
    const root = $('#dynamicObjects');
    const svg = $('#previewSvg');
    if (!root || !svg) return;
    const renderedIds = new Set($$('.svg-object', svg).filter((element) => element.parentElement !== root).map((element) => element.dataset.target));
    root.innerHTML = '';
    const dynamicObjects = (Array.isArray(state.objects) ? state.objects : []).filter((object) => object && object.id && !renderedIds.has(object.id));
    const ns = 'http://www.w3.org/2000/svg';
    dynamicObjects.forEach((object, index) => {
      const column = index % 3;
      const row = Math.floor(index / 3);
      const x = 125 + column * 325;
      const y = 70 + row * 105;
      const group = document.createElementNS(ns, 'g');
      group.setAttribute('class', 'svg-object svg-dynamic-object');
      group.setAttribute('data-target', object.id);
      group.setAttribute('data-pivot', '0 0');
      group.setAttribute('data-base-transform', 'translate(' + x + ' ' + y + ')');
      group.setAttribute('transform', 'translate(' + x + ' ' + y + ')');
      const body = document.createElementNS(ns, 'rect');
      body.setAttribute('x', '-64');
      body.setAttribute('y', '-28');
      body.setAttribute('width', '128');
      body.setAttribute('height', '56');
      body.setAttribute('rx', '10');
      body.setAttribute('fill', '#f7f7f7');
      body.setAttribute('stroke', '#5c5c5c');
      body.setAttribute('stroke-width', '2');
      group.appendChild(body);
      const marker = document.createElementNS(ns, 'circle');
      marker.setAttribute('cx', '-42');
      marker.setAttribute('cy', '0');
      marker.setAttribute('r', '10');
      marker.setAttribute('fill', '#bfbfbf');
      marker.setAttribute('stroke', '#1a1a1a');
      group.appendChild(marker);
      const text = document.createElementNS(ns, 'text');
      text.setAttribute('x', '8');
      text.setAttribute('y', '5');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('class', 'svg-label');
      text.textContent = objectName(object, object.id).slice(0, 12);
      group.appendChild(text);
      root.appendChild(group);
    });
  }

  function applyPreview() {
    const svg = $('#previewSvg');
    const canvas = $('#preview3d');
    if (!svg && !canvas) return;
    if (svg) syncDynamicSvgObjects();
    const time = finiteOr(state.playhead_s, 0);
    const visuals = new Map();
    const svgObjects = svg ? $$('.svg-object', svg) : [];
    (Array.isArray(state.objects) ? state.objects : []).forEach((object) => {
      if (!object || !object.id) return;
      visuals.set(object.id, { opacity: 1, x: 0, y: 0, z: 0, rotation: 0, rotationAxis: 'Z', scale: 1, flash: false, material: false, materialValue: '', appeared: false, labelValue: null });
    });
    svgObjects.forEach((element) => {
      visuals.set(element.dataset.target, { opacity: 1, x: 0, y: 0, z: 0, rotation: 0, rotationAxis: 'Z', scale: 1, flash: false, material: false, materialValue: '', appeared: false, labelValue: null });
      element.classList.toggle('selected', element.dataset.target === state.selectedObjectId);
      element.style.filter = '';
      element.style.visibility = 'visible';
    });
    const label = svg ? $('#svgLabelText') : null;
    if (label) label.textContent = currentStep() ? currentStep().name : '动画说明';
    const clips = allClips().filter((clip) => clip && clip.enabled !== false).slice().sort((a, b) => finiteOr(a.start_s, 0) - finiteOr(b.start_s, 0));
    clips.forEach((clip) => {
      const visual = visuals.get(clip.target_ref);
      if (!visual) return;
      const start = finiteOr(clip.start_s, 0);
      const end = Math.max(start, finiteOr(clip.end_s, start));
      const active = time >= start && time <= end;
      if (clip.kind === 'appear') {
        if (time < start && !visual.appeared) visual.opacity = 0;
        if (time >= start) {
          visual.appeared = true;
          const frame = frameAtAbsoluteTime(clip, time);
          visual.opacity = clamp(finiteOr(frame.value, time >= end ? 1 : 0), 0, 1);
        }
      } else if (clip.kind === 'move' && time >= start) {
        const frame = frameAtAbsoluteTime(clip, time);
        if (frame.position_cm) {
          visual.x = finiteOr(frame.position_cm.x, visual.x);
          visual.y = finiteOr(frame.position_cm.y, visual.y);
          visual.z = finiteOr(frame.position_cm.z, visual.z);
        }
      } else if (clip.kind === 'rotate' && time >= start) {
        const frame = frameAtAbsoluteTime(clip, time);
        if (frame.rotation_deg != null) visual.rotation = finiteOr(frame.rotation_deg, visual.rotation);
        visual.rotationAxis = String((clip.params || {}).axis || 'Z').toUpperCase();
      } else if (clip.kind === 'scale' && time >= start) {
        const frame = frameAtAbsoluteTime(clip, time);
        if (frame.scale != null) visual.scale = Math.max(.01, finiteOr(frame.scale, visual.scale));
      } else if (clip.kind === 'flash' && active) {
        const frame = frameAtAbsoluteTime(clip, time);
        visual.flash = finiteOr(frame.value, 0) > .5;
        visual.opacity = visual.flash ? 1 : Math.min(visual.opacity, .35);
      } else if (clip.kind === 'material' && time >= start) {
        visual.materialValue = clip.params && clip.params.value ? String(clip.params.value) : '';
        visual.material = !!visual.materialValue && visual.materialValue.toLowerCase() !== 'normal';
      } else if (clip.kind === 'label' && time >= start) {
        visual.labelValue = clip.params && clip.params.value ? clip.params.value : (currentStep() ? currentStep().name : '动画说明');
      }
    });
    if (label) {
      const labelVisual = visuals.get('label');
      if (labelVisual && labelVisual.labelValue) label.textContent = labelVisual.labelValue;
    }
    const offset = state.stage_offset || { x: 0, y: 0 };
    if (svg) {
      const sceneRoot = $('#sceneRoot');
      if (sceneRoot) sceneRoot.setAttribute('transform', 'translate(' + finiteOr(offset.x, 0) + ' ' + finiteOr(offset.y, 0) + ')');
      svgObjects.forEach((element) => {
        const visual = visuals.get(element.dataset.target) || { opacity: 1, x: 0, y: 0, z: 0, rotation: 0, rotationAxis: 'Z', scale: 1, flash: false, material: false, materialValue: '' };
        element.style.opacity = String(clamp(visual.opacity, 0, 1));
        element.style.visibility = visual.opacity <= .001 ? 'hidden' : 'visible';
        const transform = element.dataset.baseTransform ? [element.dataset.baseTransform] : [];
        if (Math.abs(visual.x) > .001 || Math.abs(visual.y) > .001) transform.push('translate(' + (visual.x * .5) + ' ' + (-visual.y * .5) + ')');
        if (Math.abs(visual.rotation) > .001) transform.push('rotate(' + visual.rotation + ' ' + (element.dataset.pivot || svgPivot(element.dataset.target)) + ')');
        if (Math.abs(visual.scale - 1) > .001) transform.push('scale(' + visual.scale + ')');
        element.setAttribute('transform', transform.join(' '));
        const filters = [];
        if (visual.flash) filters.push('drop-shadow(0 0 7px rgba(180,71,8,.75))');
        if (visual.material) filters.push('sepia(1) saturate(2)');
        element.style.filter = filters.join(' ');
      });
      const outline = $('#selectionOutline');
      const selected = svgObjectForTarget(svg, state.selectedObjectId);
      if (outline && selected) {
        try {
          const box = selected.getBBox();
          outline.setAttribute('visibility', 'visible');
          outline.querySelector('rect').setAttribute('x', box.x - 7);
          outline.querySelector('rect').setAttribute('y', box.y - 7);
          outline.querySelector('rect').setAttribute('width', box.width + 14);
          outline.querySelector('rect').setAttribute('height', box.height + 14);
        } catch (error) {
          outline.setAttribute('visibility', 'hidden');
        }
      } else if (outline) outline.setAttribute('visibility', 'hidden');
    }
    $('#stageHint').textContent = state.selectedClipId ? '已选择动作：' + actionName((selectedClip() || {}).kind) : '选择左侧对象或时间轴片段查看动作';
    render3DScene(visuals);
  }

  function toggleGrid() {
    state.grid = !state.grid;
    const grid = $('#gridRect');
    if (grid) grid.style.display = state.grid ? '' : 'none';
    applyPreview();
  }

  function setStageTool(tool) {
    stageTool = ['select', 'orbit', 'pan'].includes(tool) ? tool : 'select';
    $$('[data-tool]').forEach((button) => button.classList.toggle('active', button.dataset.tool === stageTool));
    const viewport = $('#stageViewport');
    if (viewport) {
      viewport.classList.toggle('pan-mode', stageTool === 'pan');
      viewport.classList.toggle('orbit-mode', stageTool === 'orbit');
    }
    const canvas = $('#preview3d');
    if (canvas) {
      canvas.classList.toggle('select-mode', stageTool === 'select');
      canvas.classList.toggle('pan-mode', stageTool === 'pan');
      canvas.classList.toggle('orbit-mode', stageTool === 'orbit');
    }
  }

  function fitStage() {
    state.stage_offset = { x: 0, y: 0 };
    camera3d.yaw = -0.72;
    camera3d.pitch = 0.48;
    camera3d.distance = 760;
    camera3d.target = { x: 0, y: 0, z: 85 };
    camera3d.panX = 0;
    camera3d.panY = 0;
    applyPreview();
    toast('视口已适配', 'ok');
  }

  function handleAction(action, event) {
    if (action === 'save') return saveDraft();
    if (action === 'export') { setView('export'); return; }
    if (action === 'import') return $('#fileInput').click();
    if (action === 'new-spec') return newSpec();
    if (action === 'reset-demo') return resetDemo();
    if (action === 'generate') return generateDraft(false);
    if (action === 'open-editor') { setView('editor'); return; }
    if (action === 'open-library') { inspectorTab = 'library'; renderInspectors(); return; }
    if (action === 'add-step') return addStep();
    if (action === 'collapse-all') { const key = 'root.' + state.template_id; state.collapsedGroups[key] = !state.collapsedGroups[key]; renderStructure(); return; }
    if (action === 'toggle-play') return togglePlay();
    if (action === 'step-back') { state.playhead_s = clamp(state.playhead_s - .5, 0, state.duration_s); renderTimeline(); applyPreview(); return; }
    if (action === 'step-forward') { state.playhead_s = clamp(state.playhead_s + .5, 0, state.duration_s); renderTimeline(); applyPreview(); return; }
    if (action === 'undo') return undo();
    if (action === 'redo') return redo();
    if (action === 'add-clip') return addCustomClip('move');
    if (action === 'add-keyframe') return addKeyframe();
    if (action === 'delete-clip') return deleteClip();
    if (action === 'validate') return runValidation();
    if (action === 'download') return downloadManifest();
    if (action === 'copy-manifest') return copyManifest();
    if (action === 'copy-a-route') return copyARouteSample();
    if (action === 'open-help') return openHelp();
    if (action === 'toggle-grid') return toggleGrid();
    if (action === 'fit') return fitStage();
    if (action === 'add-object') return addObject();
  }

  function bindEvents() {
    document.addEventListener('click', (event) => {
      const toolButton = event.target.closest('[data-tool]');
      if (toolButton) { setStageTool(toolButton.dataset.tool); return; }
      const viewButton = event.target.closest('[data-view]');
      if (viewButton) { setView(viewButton.dataset.view); return; }
      const actionButton = event.target.closest('[data-action]');
      if (actionButton) { handleAction(actionButton.dataset.action, event); return; }
      const templateButton = event.target.closest('[data-template]');
      if (templateButton) { switchTemplate(templateButton.dataset.template); return; }
      const node = event.target.closest('[data-structure-node]');
      if (node) { selectStep(node.dataset.structureNode); return; }
      const group = event.target.closest('[data-structure-group]');
      if (group) { state.collapsedGroups[group.dataset.structureGroup] = !state.collapsedGroups[group.dataset.structureGroup]; renderStructure(); return; }
      const editorStep = event.target.closest('[data-editor-step]');
      if (editorStep) { selectStep(editorStep.dataset.editorStep); setView('editor'); return; }
      const objectRow = event.target.closest('[data-object-id]');
      if (objectRow) { selectObject(objectRow.dataset.objectId); return; }
      const clip = event.target.closest('[data-clip-id]');
      if (clip) { selectClip(clip.dataset.clipId); return; }
      const inspectorTabButton = event.target.closest('[data-inspector]');
      if (inspectorTabButton) { inspectorTab = inspectorTabButton.dataset.inspector; renderInspectors(); return; }
      const libraryTabButton = event.target.closest('[data-library-tab]');
      if (libraryTabButton) { libraryTab = libraryTabButton.dataset.libraryTab; renderLibraryInspector(); return; }
      const libraryCard = event.target.closest('[data-library-id]');
       if (libraryCard) { const item = library.find((entry) => entry.id === libraryCard.dataset.libraryId); if (item) addCustomClip(item.kind, null, null, null, { asset_ref: item.asset_ref }); return; }
      const deleteKf = event.target.closest('[data-delete-kf]');
      if (deleteKf) { deleteKeyframe(Number(deleteKf.dataset.deleteKf)); return; }
    });

    document.addEventListener('change', (event) => {
      if (event.target.id === 'fileInput' && event.target.files && event.target.files[0]) { handleImport(event.target.files[0]); event.target.value = ''; return; }
      if (event.target.id === 'packageName') { state.package_name = event.target.value; markDirty('已更新行为包名称'); renderExport(); return; }
      if (event.target.id === 'exportRange') { state.export_range = event.target.value; markDirty('已更新导出范围'); renderExport(); return; }
      if (event.target.id === 'exportFormat') { state.export_format = event.target.value; markDirty('已更新行为包格式'); renderExport(); return; }
      const objectField = event.target.closest('[data-object-field]');
      const selectedObject = getObject(state.selectedObjectId);
      if (objectField && selectedObject) {
        if (selectedObject[objectField.dataset.objectField] !== objectField.value.trim()) pushHistory();
        if (updateObjectBinding(selectedObject, objectField.dataset.objectField, objectField.value)) {
          markDirty('已更新对象绑定');
          renderAll();
        }
        return;
      }
      if (event.target.id === 'speedSelect') return;
      const clipField = event.target.closest('[data-clip-field]');
      const clip = selectedClip();
      if (clipField && clip) { pushHistory(); updateClipField(clip, clipField.dataset.clipField, clipField.type === 'checkbox' ? clipField.checked : clipField.value); markDirty('已更新动作属性'); renderTimeline(); renderClipInspector(); renderExport(); applyPreview(); return; }
      const paramField = event.target.closest('[data-param]');
      if (paramField && clip) { pushHistory(); updateClipParam(clip, paramField.dataset.param, paramField.value); markDirty('已更新动作参数'); renderTimeline(); renderClipInspector(); renderExport(); applyPreview(); return; }
      const kfField = event.target.closest('[data-kf-field]');
      if (kfField && clip) {
        pushHistory();
        const index = Number(kfField.dataset.kfIndex);
        if (clip.keyframes[index]) updateKeyframeField(clip.keyframes[index], kfField.dataset.kfField, kfField.value);
        clip.manual = true;
        clip.generated = false;
        markDirty('已更新关键帧');
        renderClipInspector();
        renderExport();
        applyPreview();
      }
    });

    document.addEventListener('input', (event) => {
      const objectField = event.target.closest('[data-object-field]');
      const selectedObject = getObject(state.selectedObjectId);
      if (objectField && selectedObject) {
        updateObjectBinding(selectedObject, objectField.dataset.objectField, objectField.value);
        return;
      }
      if (event.target.dataset.librarySearch !== undefined) {
        const query = event.target.value.toLowerCase();
        $$('.library-card', $('#inspector-library')).forEach((card) => { card.hidden = !card.textContent.toLowerCase().includes(query); });
      }
    });

    $('#previewSvg').addEventListener('click', (event) => {
      if (stageTool !== 'select') return;
      const target = event.target.closest('.svg-object');
      if (target && target.dataset.target) selectObject(target.dataset.target);
    });
    const canvas3d = $('#preview3d');
    if (canvas3d) {
      canvas3d.addEventListener('pointerdown', (event) => {
        const requestedMode = stageTool === 'select' && !event.shiftKey && event.button === 0 ? 'select' : (stageTool === 'pan' || event.shiftKey || event.button === 1 ? 'pan' : 'orbit');
        stageDrag = { mode: requestedMode, x: event.clientX, y: event.clientY, moved: false };
        canvas3d.setPointerCapture(event.pointerId);
        event.preventDefault();
      });
      canvas3d.addEventListener('pointermove', (event) => {
        if (!stageDrag) return;
        const dx = event.clientX - stageDrag.x; const dy = event.clientY - stageDrag.y;
        if (Math.abs(dx) + Math.abs(dy) > 3) stageDrag.moved = true;
        stageDrag.x = event.clientX; stageDrag.y = event.clientY;
        // In select mode a click picks an object, while a drag naturally
        // becomes orbiting. This keeps the default gesture discoverable and
        // avoids making users switch tools just to inspect the model.
        if (stageDrag.mode === 'select' && stageDrag.moved) stageDrag.mode = 'orbit';
        if (stageDrag.mode === 'orbit') {
          camera3d.yaw += dx * .009;
          camera3d.pitch = clamp(camera3d.pitch + dy * .009, -1.2, 1.2);
        } else if (stageDrag.mode === 'pan') {
          camera3d.panX += dx;
          camera3d.panY += dy;
        }
        if (stageDrag.mode !== 'select' || stageDrag.moved) applyPreview();
      });
      const releasePointer = (event) => {
        if (!stageDrag) return;
        const drag = stageDrag; stageDrag = null;
        if (drag.mode === 'select' && !drag.moved && event.button === 0) {
          const targetId = pick3dObject(event.clientX, event.clientY);
          if (targetId) selectObject(targetId);
        }
      };
      canvas3d.addEventListener('pointerup', releasePointer);
      canvas3d.addEventListener('pointercancel', () => { stageDrag = null; });
      canvas3d.addEventListener('wheel', (event) => {
        camera3d.distance = clamp(camera3d.distance * Math.exp(event.deltaY * .001), 260, 2200);
        applyPreview();
        event.preventDefault();
      }, { passive: false });
      canvas3d.addEventListener('keydown', (event) => {
        const step = event.shiftKey ? .12 : .06;
        if (event.key === 'ArrowLeft') camera3d.yaw -= step;
        else if (event.key === 'ArrowRight') camera3d.yaw += step;
        else if (event.key === 'ArrowUp') camera3d.pitch = clamp(camera3d.pitch - step, -1.2, 1.2);
        else if (event.key === 'ArrowDown') camera3d.pitch = clamp(camera3d.pitch + step, -1.2, 1.2);
        else if (event.key === '+' || event.key === '=') camera3d.distance = clamp(camera3d.distance * .9, 260, 2200);
        else if (event.key === '-' || event.key === '_') camera3d.distance = clamp(camera3d.distance * 1.1, 260, 2200);
        else if (event.key === 'Home') { fitStage(); return; }
        else return;
        applyPreview();
        event.preventDefault();
      });
      canvas3d.addEventListener('dblclick', () => fitStage());
    }
    $('#timelineViewport').addEventListener('click', (event) => {
      if (event.target.closest('.timeline-clip')) return;
      setPlayheadFromPointer(event);
    });
    $('#timelineViewport').addEventListener('dragover', (event) => { if (event.target.closest('[data-drop-target]')) event.preventDefault(); });
    $('#timelineViewport').addEventListener('drop', (event) => {
      event.preventDefault();
      const itemId = event.dataTransfer.getData('text/plain') || draggedLibraryId;
      const item = library.find((entry) => entry.id === itemId);
      const row = event.target.closest('[data-track-id]');
      const track = row ? state.tracks.find((candidate) => candidate.id === row.dataset.trackId) : null;
       if (item) addCustomClip(item.kind, track ? track.target_ref : null, state.selectedStepId, timeFromTimelinePointer(event), { asset_ref: item.asset_ref });
    });
    document.addEventListener('dragstart', (event) => {
      const card = event.target.closest('[data-library-id]');
      if (!card) return;
      draggedLibraryId = card.dataset.libraryId;
      event.dataTransfer.setData('text/plain', draggedLibraryId);
      event.dataTransfer.effectAllowed = 'copy';
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && $('#modalRoot') && !$('#modalRoot').hidden && $('#modalRoot')._close) $('#modalRoot')._close();
      if (event.code === 'Space' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) { event.preventDefault(); togglePlay(); }
    });
  }

  function init3dViewport() {
    const canvas = $('#preview3d');
    if (!canvas) return;
    if (window.ResizeObserver) {
      renderer3d.resizeObserver = new ResizeObserver(() => {
        if (!$('#view-editor') || !$('#view-editor').hidden) applyPreview();
      });
      renderer3d.resizeObserver.observe(canvas);
    }
    window.addEventListener('resize', () => {
      if (!$('#view-editor') || !$('#view-editor').hidden) applyPreview();
    });
    canvas.addEventListener('contextmenu', (event) => event.preventDefault());
    setStageTool(stageTool);
  }

  function boot() {
    const restored = loadDraft();
    bindEvents();
    init3dViewport();
    renderAll();
    if (restored) {
      $('#footerMessage').textContent = '已恢复本机最近草稿';
      toast('已恢复最近一次本地草稿', 'ok');
    }
    $('#gridRect').style.display = state.grid ? '' : 'none';
  }

  boot();
})();
