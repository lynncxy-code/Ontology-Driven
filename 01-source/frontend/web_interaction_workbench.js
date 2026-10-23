(function registerWebInteractionWorkbench(global) {
  "use strict";

  const { reactive, ref, computed, watch, onMounted, nextTick } = Vue;
  const clone = value => JSON.parse(JSON.stringify(value));
  const emptyConfig = () => ({ pages: [], business_views: [], bindings: [], web_policy: { allowed_hosts: [] } });
  const cleanList = value => String(value || "").split(",").map(item => item.trim()).filter(Boolean);
  const BACKUP_KEY = "ontotwin.web-interaction.3.8.2.conflict-backup";

  global.OntoTwinWebWorkbench = {
    emits: ["dirty-change", "toast"],
    template: `
      <div class="business-console">
        <header class="business-topbar">
          <div class="business-context">
            <span class="eyebrow">业务配置台</span>
            <strong>{{ projectName || '正在读取项目' }}</strong>
            <span class="code">{{ projectId || '--' }}</span>
          </div>
          <div class="business-actions">
            <span class="save-state" :class="{dirty}">{{ dirty ? '有未应用修改' : '已与运行端同步' }}</span>
            <span class="revision">版本 {{ revision }}</span>
            <button class="btn" @click="advancedOpen=true">高级</button>
            <button class="btn btn-primary" :disabled="busy||!dirty" @click="applyChanges(false)">{{ busy ? '正在应用…' : '保存并应用' }}</button>
          </div>
        </header>

        <div v-if="loading" class="loading">正在加载业务配置…</div>
        <div v-else class="business-layout">
          <aside class="business-list-panel">
            <div class="panel-head">
              <div><h2>业务</h2><span>{{ draft.business_views.length }} 项</span></div>
              <button class="btn btn-sm" @click="openCreate">新建</button>
            </div>
            <div class="panel-search"><input class="field" v-model.trim="businessQuery" placeholder="搜索业务"></div>
            <div class="business-list" role="list" aria-label="业务列表">
              <div v-for="view in filteredViews" :key="view.business_view_id" class="business-list-item" role="listitem">
                <button class="business-row" :class="{active:view.business_view_id===selectedBusinessId}"
                  @click="selectBusiness(view.business_view_id)">
                  <span class="business-row-copy"><strong>{{ view.name || '未命名业务' }}</strong><small>{{ businessMemberIds(view).length }} 个对象 · {{ view.enabled===false?'已停用':'已启用' }}</small></span>
                  <span class="state-dot" :class="view.enabled===false?'off':'on'" aria-hidden="true"></span>
                </button>
                <button v-if="view.business_view_id===selectedBusinessId" class="btn btn-ghost btn-sm business-row-delete danger-text"
                  :aria-label="'删除业务 '+(view.name||view.business_view_id)" @click.stop="requestDeleteBusiness(view)">删除</button>
              </div>
              <div v-if="!filteredViews.length" class="empty-state">
                <strong>{{ draft.business_views.length ? '没有匹配结果' : '还没有业务' }}</strong>
                <p v-if="!draft.business_views.length">新建业务后，直接勾选场景对象作为成员。</p>
              </div>
            </div>
          </aside>

          <main class="member-panel">
            <template v-if="selectedBusiness">
              <div class="member-head">
                <div>
                  <span class="eyebrow">当前业务</span>
                  <h1>{{ selectedBusiness.name || '未命名业务' }}</h1>
                  <p>{{ selectedBusiness.description || '从对象列表中选择该业务需要管理的设备。' }}</p>
                </div>
              </div>

              <div class="member-toolbar">
                <input class="field" v-model.trim="memberQuery" placeholder="搜索对象名称、ID、类型或分区">
                <div class="segmented member-filter" aria-label="对象范围">
                  <button class="segment" :class="{active:memberFilter==='members'}" @click="memberFilter='members'">业务内 {{ currentMemberIds.length }}</button>
                  <button class="segment" :class="{active:memberFilter==='all'}" @click="memberFilter='all'">全部 {{ instances.length }}</button>
                  <button class="segment" :class="{active:memberFilter==='outside'}" @click="memberFilter='outside'">未加入 {{ Math.max(0,instances.length-currentMemberIds.length) }}</button>
                </div>
              </div>

              <div class="member-summary">
                <span>勾选即加入，取消即移出</span>
                <span v-if="unzonedCount" class="warning-copy">{{ unzonedCount }} 个对象尚未分区</span>
              </div>
              <div class="member-list" role="list" aria-label="对象成员">
                <div v-for="item in filteredInstances" :key="item.id" class="member-row" :class="{selected:item.id===selectedInstanceId}" role="listitem" tabindex="0" :aria-current="item.id===selectedInstanceId ? 'true' : undefined" @click="selectInstance(item.id)" @keydown.enter.prevent="selectInstance(item.id)" @keydown.space.prevent="selectInstance(item.id)">
                  <span class="member-check" @click.stop>
                    <input type="checkbox" :checked="isMember(item.id)" :aria-label="'切换 '+instanceName(item)+' 的业务成员状态'" @change="selectInstance(item.id); toggleMembership(item.id,$event.target.checked)">
                  </span>
                  <span class="member-primary"><strong>{{ instanceName(item) }}</strong><small>{{ typeName(item.object_type_rid) }}</small></span>
                  <span class="member-zone">{{ zoneName(item.zone_id) }}</span>
                  <span class="member-id code">{{ item.id }}</span>
                </div>
                <div v-if="!filteredInstances.length" class="empty-state compact"><strong>当前筛选下没有对象</strong><p>切换范围或清空搜索词后再试。</p></div>
              </div>
            </template>
            <div v-else class="empty-stage">
              <div><strong>选择一个业务开始配置</strong><p>左侧管理业务，中间选择成员，右侧设置场景与页面行为。</p><button class="btn btn-primary" @click="openCreate">新建业务</button></div>
            </div>
          </main>

          <aside class="property-panel">
            <template v-if="selectedBusiness">
              <section class="property-section">
                <div class="property-title"><h2>业务属性</h2><label class="switch-label"><input type="checkbox" v-model="selectedBusiness.enabled">启用</label></div>
                <label class="form-row"><span class="label">名称</span><input class="field" v-model.trim="selectedBusiness.name"></label>
                <label class="form-row"><span class="label">说明</span><textarea class="field" rows="3" v-model.trim="selectedBusiness.description" placeholder="说明这个业务用于什么场景"></textarea></label>
              </section>
              <section class="property-section">
                <h2>激活业务时的场景</h2>
                <p class="section-help">仅在通过运行 Dock 或网页入口激活该业务时生效，不影响直接点击对象。</p>
                <label class="choice-card" :class="{active:sceneBehavior==='isolate_focus'}"><input type="radio" value="isolate_focus" v-model="sceneBehavior"><span><strong>聚焦业务对象</strong><small>镜头适配并只显示业务范围，适合日常使用。</small></span></label>
                <label class="choice-card" :class="{active:sceneBehavior==='highlight'}"><input type="radio" value="highlight" v-model="sceneBehavior"><span><strong>高亮业务对象</strong><small>保留周边场景作为空间参照。</small></span></label>
                <label class="choice-card" :class="{active:sceneBehavior==='web_only'}"><input type="radio" value="web_only" v-model="sceneBehavior"><span><strong>不改变场景</strong><small>仅打开绑定页面。</small></span></label>
              </section>
              <section class="property-section">
                <h2>业务入口页面</h2>
                <label class="form-row"><span class="label">激活该业务时打开</span>
                  <select class="field" :value="businessPageId" @change="setBusinessPage($event.target.value)">
                    <option value="">不打开网页</option>
                    <option v-for="page in enabledPages" :key="page.page_id" :value="page.page_id">{{ page.name || page.page_id }}</option>
                  </select>
                </label>
                <p class="hint">网页与业务对象强绑定；运行时网页保持打开，也可以继续使用 Dock 和场景交互。</p>
              </section>
              <section class="property-section current-selection">
                <h2>当前选择</h2>
                <template v-if="selectedInstance">
                  <div class="selection-name"><strong>{{ instanceName(selectedInstance) }}</strong><span :class="isMember(selectedInstance.id)?'included':'excluded'">{{ isMember(selectedInstance.id) ? '业务内' : '业务外' }}</span></div>
                  <dl class="property-list"><div><dt>实例 ID</dt><dd class="code">{{ selectedInstance.id }}</dd></div><div><dt>类型</dt><dd>{{ typeName(selectedInstance.object_type_rid) }}</dd></div><div><dt>分区</dt><dd>{{ zoneName(selectedInstance.zone_id) }}</dd></div></dl>
                  <button class="btn btn-sm" @click="toggleMembership(selectedInstance.id,!isMember(selectedInstance.id))">{{ isMember(selectedInstance.id) ? '移出当前业务' : '加入当前业务' }}</button>
                  <div class="object-page-setting">
                    <label class="form-row"><span class="label">点击对象时打开</span>
                      <select class="field" :value="instanceDetailChoice" @change="setInstanceDetailPage($event.target.value)">
                        <option value="__inherit__">{{ inheritedDetailLabel }}</option>
                        <option value="__block__">不打开网页（仅此对象）</option>
                        <option v-for="page in enabledPages" :key="'instance-'+page.page_id" :value="page.page_id">{{ page.name || page.page_id }}</option>
                      </select>
                    </label>
                    <p class="hint">保存并应用后，在普通运行状态下一次点击该对象即打开页面，并自动传入实例 ID。</p>
                  </div>
                </template>
                <p v-else class="hint">单击中间列表中的对象，在这里查看属性。</p>
              </section>
            </template>
          </aside>
        </div>

        <div v-if="createDialog.open" class="modal-mask" @click.self="closeCreate">
          <form class="modal" @submit.prevent="createBusiness">
            <h3>新建业务</h3><p>先给业务命名，成员和行为稍后在同一页配置。</p>
            <label class="form-row modal-field"><span class="label">业务名称</span><input ref="createNameInput" class="field" v-model.trim="createDialog.name" placeholder="例如：能源管理"></label>
            <div class="modal-foot"><button type="button" class="btn btn-ghost" @click="closeCreate">取消</button><button class="btn btn-primary" :disabled="!createDialog.name">创建</button></div>
          </form>
        </div>

        <div v-if="advancedOpen" class="modal-mask" @click.self="advancedOpen=false">
          <div class="modal advanced-modal" role="dialog" aria-modal="true" aria-label="高级设置">
            <div class="advanced-head"><div><span class="eyebrow">高级设置</span><h3>页面资源与版本</h3></div><button class="btn btn-ghost icon-close" aria-label="关闭" @click="advancedOpen=false">×</button></div>
            <section class="advanced-section">
              <div class="section-line"><div><strong>页面资源</strong><span>仅在需要新增或修改网页地址时使用</span></div><button class="btn btn-sm" @click="addPage">新增页面</button></div>
              <div class="page-editor-list">
                <article v-for="(page,index) in draft.pages" :key="page.page_id||index" class="page-editor-card">
                  <div class="page-editor-grid"><label class="form-row"><span class="label">名称</span><input class="field" v-model.trim="page.name"></label><label class="form-row"><span class="label">页面地址</span><input class="field" v-model.trim="page.base_url"></label></div>
                  <div class="page-editor-foot"><span class="code">{{ page.page_id }}</span><label class="switch-label"><input type="checkbox" v-model="page.enabled">启用</label><button class="btn btn-ghost btn-sm danger-text" @click="requestDeletePage(index)">删除</button></div>
                </article>
                <div v-if="!draft.pages.length" class="empty-state compact"><strong>没有页面资源</strong></div>
              </div>
            </section>
            <section class="advanced-section">
              <strong>允许的网页域名</strong><p class="hint">多个域名用英文逗号分隔。</p>
              <input class="field" :value="allowedHostsText" @change="setAllowedHosts($event.target.value)" placeholder="localhost, example.com">
            </section>
            <section class="advanced-section">
              <div class="section-line"><div><strong>版本与恢复</strong><span>当前版本 {{ revision }}</span></div><div class="inline-actions"><button v-if="hasConflictBackup" class="btn btn-sm" @click="restoreConflictBackup">恢复冲突备份</button><button class="btn btn-sm" :disabled="busy||!hasPrevious" @click="requestRollback">回滚上一版本</button></div></div>
            </section>
            <section v-if="validation" class="advanced-section validation-summary">
              <strong>配置检查</strong><span v-if="validation.valid&&!validation.warnings.length">没有发现问题</span><span v-else>{{ validation.errors.length }} 个错误，{{ validation.warnings.length }} 个提醒</span>
              <div v-for="item in validation.errors.slice(0,6)" :key="item.path+item.code" class="validation-row error">{{ friendlyMessage(item.message) }}</div>
              <div v-for="item in validation.warnings.slice(0,6)" :key="item.path+item.code" class="validation-row warning">{{ friendlyMessage(item.message) }}</div>
            </section>
            <div class="modal-foot"><button class="btn" @click="advancedOpen=false">完成</button></div>
          </div>
        </div>

        <div v-if="dialog.open" class="modal-mask" @click.self="closeDialog">
          <div class="modal" role="dialog" aria-modal="true"><h3>{{ dialog.title }}</h3><p>{{ dialog.body }}</p><div class="modal-foot"><button class="btn btn-ghost" @click="closeDialog">取消</button><button class="btn btn-primary" @click="confirmDialog">{{ dialog.confirmText }}</button></div></div>
        </div>
      </div>
    `,
    setup(_, { emit }) {
      const loading = ref(true), busy = ref(false), dirty = ref(false), hydrating = ref(false);
      const projectId = ref(""), projectName = ref(""), revision = ref(0), hasPrevious = ref(false), unzonedCount = ref(0);
      const draft = reactive(emptyConfig());
      const zones = ref([]), objectTypes = ref([]), instances = ref([]), validation = ref(null);
      const selectedBusinessId = ref(""), selectedInstanceId = ref("");
      const businessQuery = ref(""), memberQuery = ref(""), memberFilter = ref("members");
      const advancedOpen = ref(false), createNameInput = ref(null);
      const createDialog = reactive({ open: false, name: "" });
      const dialog = reactive({ open: false, title: "", body: "", confirmText: "确认", action: null });

      const notify = (message, type = "") => emit("toast", message, type);
      const selectedBusiness = computed(() => draft.business_views.find(item => item.business_view_id === selectedBusinessId.value) || null);
      const selectedInstance = computed(() => instances.value.find(item => item.id === selectedInstanceId.value) || null);
      const filteredViews = computed(() => {
        const query = businessQuery.value.toLocaleLowerCase();
        return draft.business_views.filter(item => !query || `${item.name || ""} ${item.business_view_id || ""}`.toLocaleLowerCase().includes(query));
      });
      const currentMemberIds = computed(() => businessMemberIds(selectedBusiness.value));
      const filteredInstances = computed(() => {
        const members = new Set(currentMemberIds.value), query = memberQuery.value.toLocaleLowerCase();
        return instances.value.filter(item => {
          const included = members.has(item.id);
          if (memberFilter.value === "members" && !included) return false;
          if (memberFilter.value === "outside" && included) return false;
          return !query || `${instanceName(item)} ${item.id} ${typeName(item.object_type_rid)} ${zoneName(item.zone_id)}`.toLocaleLowerCase().includes(query);
        });
      });
      const sceneBehavior = computed({
        get: () => selectedBusiness.value?.scene_behavior || "isolate_focus",
        set: value => { if (selectedBusiness.value) selectedBusiness.value.scene_behavior = value; },
      });
      const enabledPages = computed(() => draft.pages.filter(item => item.enabled !== false));
      const businessBinding = computed(() => draft.bindings.find(item => item.trigger === "business_view_activated" && item.scope?.business_view_id === selectedBusinessId.value) || null);
      const businessPageId = computed(() => businessBinding.value?.effect === "open_web" ? (businessBinding.value.page_id || "") : "");
      const instanceDetailBinding = computed(() => selectedInstance.value ? findDetailBinding({ instance_id: selectedInstance.value.id }) : null);
      const inheritedDetailBinding = computed(() => {
        const item = selectedInstance.value;
        if (!item) return null;
        return [
          item.zone_id && item.object_type_rid ? { zone_id: item.zone_id, object_type_rid: item.object_type_rid } : null,
          item.object_type_rid ? { object_type_rid: item.object_type_rid } : null,
          item.zone_id ? { zone_id: item.zone_id } : null,
          {},
        ].filter(Boolean).map(findDetailBinding).find(Boolean) || null;
      });
      const instanceDetailChoice = computed(() => {
        const binding = instanceDetailBinding.value;
        if (!binding) return "__inherit__";
        return binding.effect === "open_web" && binding.page_id ? binding.page_id : "__block__";
      });
      const inheritedDetailLabel = computed(() => {
        const binding = inheritedDetailBinding.value;
        if (!binding) return "继承已有规则（当前未配置）";
        if (binding.effect !== "open_web") return "继承已有规则（当前不打开网页）";
        const page = draft.pages.find(item => item.page_id === binding.page_id);
        return `继承已有规则（${page?.name || binding.page_id || "页面不可用"}）`;
      });
      const allowedHostsText = computed(() => (draft.web_policy?.allowed_hosts || []).join(", "));
      const hasConflictBackup = computed(() => !!localStorage.getItem(BACKUP_KEY));

      function scopeEquals(left, right) {
        const clean = value => Object.fromEntries(Object.entries(value || {}).filter(([, item]) => item !== null && item !== undefined && item !== ""));
        return JSON.stringify(Object.entries(clean(left)).sort()) === JSON.stringify(Object.entries(clean(right)).sort());
      }
      function findDetailBinding(scope) {
        return draft.bindings.find(item => item.trigger === "open_detail" && item.enabled !== false && scopeEquals(item.scope, scope)) || null;
      }

      function normalizeDraft(value) {
        const next = clone(value || emptyConfig());
        next.pages = Array.isArray(next.pages) ? next.pages : [];
        next.business_views = Array.isArray(next.business_views) ? next.business_views : [];
        next.bindings = Array.isArray(next.bindings) ? next.bindings : [];
        next.web_policy = next.web_policy && typeof next.web_policy === "object" ? next.web_policy : { allowed_hosts: [] };
        next.web_policy.allowed_hosts = Array.isArray(next.web_policy.allowed_hosts) ? next.web_policy.allowed_hosts : [];
        next.business_views.forEach(view => {
          view.rule_groups = Array.isArray(view.rule_groups) ? view.rule_groups : [];
          view.exclude_instance_ids = Array.isArray(view.exclude_instance_ids) ? view.exclude_instance_ids : [];
          view.scene_behavior = view.scene_behavior || "isolate_focus";
        });
        return next;
      }
      function assignDraft(value) {
        hydrating.value = true;
        const next = normalizeDraft(value);
        draft.pages.splice(0, draft.pages.length, ...next.pages);
        draft.business_views.splice(0, draft.business_views.length, ...next.business_views);
        draft.bindings.splice(0, draft.bindings.length, ...next.bindings);
        draft.web_policy = next.web_policy;
        dirty.value = false;
        emit("dirty-change", false);
        if (!draft.business_views.some(item => item.business_view_id === selectedBusinessId.value)) selectedBusinessId.value = draft.business_views[0]?.business_view_id || "";
        setTimeout(() => { hydrating.value = false; }, 0);
      }
      async function load() {
        loading.value = true;
        try {
          const [configRes, zoneRes, typeRes, instanceRes] = await Promise.all([
            axios.get("/api/v2/web-interactions"), axios.get("/api/v2/zones"), axios.get("/api/v2/ontology/types"), axios.get("/api/v2/instances"),
          ]);
          const data = configRes.data;
          projectId.value = data.project_id || ""; projectName.value = data.project_name || ""; revision.value = Number(data.revision || 0);
          hasPrevious.value = !!data.has_previous_published; validation.value = data.draft_validation || null;
          zones.value = zoneRes.data.zones || [];
          objectTypes.value = Array.isArray(typeRes.data) ? typeRes.data : (typeRes.data.types || []);
          instances.value = Array.isArray(instanceRes.data) ? instanceRes.data : (instanceRes.data.instances || []);
          unzonedCount.value = Number(zoneRes.data.unassigned_count || instances.value.filter(item => !item.zone_id).length);
          assignDraft(data.draft);
        } catch (error) { notify(error.response?.data?.message || "业务配置台加载失败", "err"); }
        finally { loading.value = false; }
      }
      watch(draft, () => {
        if (!hydrating.value) { dirty.value = true; emit("dirty-change", true); }
      }, { deep: true });

      function zoneId(zone) { return zone?.id || zone?.zone_id || ""; }
      function zoneName(id) { if (!id) return "未分区"; return zones.value.find(item => zoneId(item) === id)?.name || id; }
      function typeName(id) { if (!id) return "未指定类型"; return objectTypes.value.find(item => (item.rid || item.id) === id)?.name || id; }
      function instanceName(item) { return item?.display_name || item?.name || item?.id || "未命名对象"; }
      function expandedZones(ids) {
        const result = new Set(ids || []); let changed = true;
        while (changed) {
          changed = false;
          zones.value.forEach(zone => { const id = zoneId(zone); if (zone.parent_zone_id && result.has(zone.parent_zone_id) && !result.has(id)) { result.add(id); changed = true; } });
        }
        return result;
      }
      function groupMatches(group) {
        if (!["zone_ids", "object_type_rids", "instance_ids"].some(key => Array.isArray(group?.[key]) && group[key].length)) return [];
        const allowedZones = expandedZones(group.zone_ids || []);
        return instances.value.filter(item =>
          (!(group.zone_ids || []).length || allowedZones.has(item.zone_id)) &&
          (!(group.object_type_rids || []).length || group.object_type_rids.includes(item.object_type_rid)) &&
          (!(group.instance_ids || []).length || group.instance_ids.includes(item.id))
        );
      }
      function businessMemberIds(view) {
        if (!view) return [];
        const result = new Set();
        (view.rule_groups || []).forEach(group => groupMatches(group).forEach(item => result.add(item.id)));
        (view.exclude_instance_ids || []).forEach(id => result.delete(id));
        return [...result];
      }
      function isMember(id) { return currentMemberIds.value.includes(id); }
      function selectBusiness(id) { selectedBusinessId.value = id; selectedInstanceId.value = ""; memberFilter.value = "members"; }
      function selectInstance(id) { selectedInstanceId.value = id; }
      function exactGroup(view, create = false) {
        let group = (view.rule_groups || []).find(item => !(item.zone_ids || []).length && !(item.object_type_rids || []).length && Array.isArray(item.instance_ids));
        if (!group && create) { group = { zone_ids: [], object_type_rids: [], instance_ids: [] }; view.rule_groups.push(group); }
        return group;
      }
      function toggleMembership(id, enabled) {
        const view = selectedBusiness.value; if (!view) return;
        view.exclude_instance_ids = Array.isArray(view.exclude_instance_ids) ? view.exclude_instance_ids : [];
        view.rule_groups = Array.isArray(view.rule_groups) ? view.rule_groups : [];
        if (enabled) {
          view.exclude_instance_ids = view.exclude_instance_ids.filter(item => item !== id);
          if (!businessMemberIds(view).includes(id)) {
            const group = exactGroup(view, true);
            if (!group.instance_ids.includes(id)) group.instance_ids.push(id);
          }
        } else {
          view.rule_groups.forEach(group => { if (Array.isArray(group.instance_ids)) group.instance_ids = group.instance_ids.filter(item => item !== id); });
          view.rule_groups = view.rule_groups.filter(group => ["zone_ids", "object_type_rids", "instance_ids"].some(key => (group[key] || []).length));
          if (businessMemberIds(view).includes(id) && !view.exclude_instance_ids.includes(id)) view.exclude_instance_ids.push(id);
        }
      }

      function uniqueId(prefix) {
        let id = `${prefix}.${Date.now().toString(36)}`, suffix = 1;
        const used = new Set([...draft.business_views.map(item => item.business_view_id), ...draft.pages.map(item => item.page_id), ...draft.bindings.map(item => item.binding_id)]);
        while (used.has(id)) id = `${prefix}.${Date.now().toString(36)}.${suffix++}`;
        return id;
      }
      function openCreate() { createDialog.open = true; createDialog.name = ""; nextTick(() => createNameInput.value?.focus()); }
      function closeCreate() { createDialog.open = false; createDialog.name = ""; }
      function createBusiness() {
        if (!createDialog.name) return;
        const id = uniqueId("bv.custom");
        draft.business_views.push({ business_view_id: id, name: createDialog.name, description: "", enabled: true, scene_behavior: "isolate_focus", rule_groups: [], exclude_instance_ids: [] });
        selectedBusinessId.value = id; memberFilter.value = "all"; closeCreate(); notify("业务已创建，请选择成员", "ok");
      }
      function ask(title, body, confirmText, action) { Object.assign(dialog, { open: true, title, body, confirmText, action }); }
      function closeDialog() { dialog.open = false; dialog.action = null; }
      function confirmDialog() { const action = dialog.action; closeDialog(); if (typeof action === "function") action(); }
      function requestDeleteBusiness(targetView = null) {
        const view = targetView || selectedBusiness.value; if (!view) return;
        ask("删除业务", `将删除“${view.name || view.business_view_id}”及其业务页面绑定。保存并应用后生效。`, "确认删除", () => {
          const id = view.business_view_id;
          const index = draft.business_views.findIndex(item => item.business_view_id === id);
          if (index >= 0) draft.business_views.splice(index, 1);
          for (let cursor = draft.bindings.length - 1; cursor >= 0; cursor -= 1) if (draft.bindings[cursor].scope?.business_view_id === id) draft.bindings.splice(cursor, 1);
          selectedBusinessId.value = draft.business_views[Math.max(0, index - 1)]?.business_view_id || draft.business_views[0]?.business_view_id || "";
        });
      }
      function setBusinessPage(pageId) {
        const view = selectedBusiness.value; if (!view) return;
        let binding = businessBinding.value;
        if (!binding) {
          binding = { binding_id: uniqueId("bind.business"), name: `${view.name || "业务"}页面`, enabled: true, trigger: "business_view_activated", activation_mode: "explicit", effect: "block", scope: { business_view_id: view.business_view_id }, page_id: "" };
          draft.bindings.push(binding);
        }
        binding.effect = pageId ? "open_web" : "block";
        binding.page_id = pageId || "";
        binding.enabled = true;
      }
      function setInstanceDetailPage(choice) {
        const item = selectedInstance.value;
        if (!item) return;
        const scope = { instance_id: item.id };
        for (let index = draft.bindings.length - 1; index >= 0; index -= 1) {
          const binding = draft.bindings[index];
          if (binding.trigger === "open_detail" && scopeEquals(binding.scope, scope)) draft.bindings.splice(index, 1);
        }
        if (choice === "__inherit__") return;
        const page = draft.pages.find(entry => entry.page_id === choice);
        draft.bindings.push({
          binding_id: uniqueId("bind.instance"),
          name: `${instanceName(item)}点击页面`,
          enabled: true,
          trigger: "open_detail",
          activation_mode: "explicit",
          effect: choice === "__block__" ? "block" : "open_web",
          scope,
          page_id: choice === "__block__" ? "" : (page?.page_id || choice),
        });
      }
      function addPage() {
        draft.pages.push({ page_id: uniqueId("page.custom"), name: "新页面", enabled: true, base_url: "http://localhost:5000/", param_mapping: { project_id: "project_id", business_view_id: "business_id", zone_id: "space_id", instance_id: "instance_id" }, declared_extra_params: [], scope_effects: { zone: "web_and_scene", business_view: "web_and_scene", instance: "web_and_scene" } });
      }
      function requestDeletePage(index) {
        const page = draft.pages[index]; if (!page) return;
        const usage = draft.bindings.filter(item => item.page_id === page.page_id).length;
        ask("删除页面资源", usage ? `“${page.name || page.page_id}”正被 ${usage} 条绑定使用。删除后这些绑定会一并移除。` : `将删除“${page.name || page.page_id}”。`, "确认删除", () => {
          draft.pages.splice(index, 1);
          for (let cursor = draft.bindings.length - 1; cursor >= 0; cursor -= 1) if (draft.bindings[cursor].page_id === page.page_id) draft.bindings.splice(cursor, 1);
        });
      }
      function setAllowedHosts(value) { draft.web_policy.allowed_hosts = cleanList(value).map(item => item.toLocaleLowerCase()); }

      function friendlyMessage(message) { return String(message || "").replace(/BusinessView/gi, "业务").replaceAll("业务视图", "业务"); }
      function storeConflictBackup() {
        localStorage.setItem(BACKUP_KEY, JSON.stringify({ saved_at: new Date().toISOString(), project_id: projectId.value, revision: revision.value, config: clone(draft) }));
      }
      async function applyChanges(confirmWarnings) {
        busy.value = true;
        try {
          const res = await axios.post("/api/v2/web-interactions/apply", { expected_revision: revision.value, config: clone(draft), confirm_warnings: !!confirmWarnings });
          if (res.data.status === "validation_failed") { validation.value = res.data; advancedOpen.value = true; notify("有配置错误，尚未应用", "err"); return; }
          if (res.data.status === "warning_confirmation_required") {
            validation.value = res.data;
            ask("确认带提醒应用", res.data.warnings.map(item => friendlyMessage(item.message)).join("；"), "继续应用", () => applyChanges(true)); return;
          }
          revision.value = Number(res.data.revision); hasPrevious.value = true; validation.value = { valid: true, errors: [], warnings: res.data.warnings || [] };
          assignDraft(res.data.config); localStorage.removeItem(BACKUP_KEY); notify(`已应用版本 ${revision.value}`, "ok");
        } catch (error) {
          if (error.response?.status === 409) {
            storeConflictBackup();
            ask("发现较新的配置", "你的修改已在本机备份。重新加载最新版本后，可从高级设置恢复备份并重新检查。", "重新加载", load);
          } else notify(error.response?.data?.message || "保存并应用失败", "err");
        } finally { busy.value = false; }
      }
      function restoreConflictBackup() {
        try {
          const backup = JSON.parse(localStorage.getItem(BACKUP_KEY) || "null");
          if (!backup?.config || backup.project_id !== projectId.value) { notify("没有当前项目可恢复的备份", "err"); return; }
          assignDraft(backup.config); dirty.value = true; emit("dirty-change", true); advancedOpen.value = false; notify("已恢复本机备份，请检查后重新应用", "ok");
        } catch (_) { notify("冲突备份无法读取", "err"); }
      }
      function requestRollback() { ask("回滚上一版本", "上一已发布配置将作为新版本重新应用。", "确认回滚", rollback); }
      async function rollback() {
        busy.value = true;
        try { const res = await axios.post("/api/v2/web-interactions/rollback", { expected_revision: revision.value }); revision.value = Number(res.data.revision); await load(); notify(`已回滚为版本 ${revision.value}`, "ok"); }
        catch (error) { notify(error.response?.data?.message || "回滚失败", "err"); }
        finally { busy.value = false; }
      }

      onMounted(load);
      return {
        loading, busy, dirty, projectId, projectName, revision, hasPrevious, unzonedCount, draft, instances, validation,
        selectedBusinessId, selectedBusiness, selectedInstanceId, selectedInstance, businessQuery, memberQuery, memberFilter,
        filteredViews, filteredInstances, currentMemberIds, sceneBehavior, enabledPages, businessPageId,
        instanceDetailChoice, inheritedDetailLabel, allowedHostsText,
        advancedOpen, createDialog, createNameInput, dialog, hasConflictBackup,
        businessMemberIds, isMember, instanceName, zoneName, typeName, selectBusiness, selectInstance, toggleMembership,
        openCreate, closeCreate, createBusiness, requestDeleteBusiness, setBusinessPage, setInstanceDetailPage,
        addPage, requestDeletePage, setAllowedHosts,
        applyChanges, restoreConflictBackup, requestRollback, closeDialog, confirmDialog, friendlyMessage,
      };
    },
  };
})(window);
