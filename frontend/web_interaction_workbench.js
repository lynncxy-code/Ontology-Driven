(function registerWebInteractionWorkbench(global) {
  "use strict";
  const { reactive, ref, computed, watch, onMounted, nextTick } = Vue;
  const clone = value => JSON.parse(JSON.stringify(value));
  const blankConfig = () => ({ pages: [], business_views: [], bindings: [], web_policy: { allowed_hosts: [] } });
  const csv = value => Array.isArray(value) ? value.join(", ") : "";
  const parseCsv = value => String(value || "").split(",").map(item => item.trim()).filter(Boolean);
  const stableKeys = ["project_id", "business_view_id", "zone_id", "object_type_rid", "instance_id", "trigger"];

  global.OntoTwinWebWorkbench = {
    emits: ["dirty-change", "toast"],
    template: `
      <div class="web-workbench">
        <header class="web-context-bar" aria-label="当前项目上下文">
          <div class="web-context-main">
            <span class="web-context-label">当前项目</span>
            <strong>{{ projectName || '正在读取项目' }}</strong>
            <span class="web-code">{{ projectId || '--' }}</span>
          </div>
          <div class="web-context-meta">
            <span class="web-context-stat" :class="{warning:unzonedCount>0}">未分区实例 {{ unzonedCount }} 个</span>
            <span class="web-context-stat">已发布版本 {{ revision }}</span>
          </div>
        </header>

        <aside class="web-nav">
          <section class="section">
            <h2 class="section-title">工作台导航</h2>
            <div class="web-nav-list">
              <button v-for="item in sections" :key="item.id" class="web-nav-button" :class="{active:section===item.id}" @click="selectSection(item.id)">
                <span>{{ item.label }}</span><span v-if="item.count!==null" class="badge">{{ item.count }}</span>
              </button>
            </div>
          </section>
          <section class="section web-nav-guide">
            <h2 class="section-title">建议流程</h2>
            <ol><li>注册页面</li><li>管理业务范围</li><li>配置页面绑定</li><li>预览后发布</li></ol>
          </section>
        </aside>

        <main class="web-editor">
          <div v-if="loading" class="loading">正在加载页面交互配置...</div>
          <div v-else class="web-editor-inner">
            <div class="web-editor-head">
              <div><h2>{{ sectionMeta.title }}</h2><p>{{ sectionMeta.description }}</p></div>
              <button v-if="hasRecordSection&&records.length" class="btn btn-primary btn-sm" @click="addRecord">{{ sectionMeta.createLabel }}</button>
            </div>

            <section v-if="hasRecordSection&&records.length" class="web-record-picker">
              <div class="form-row">
                <label class="label">{{ sectionMeta.selectionLabel }}</label>
                <select class="field" v-model.number="selectedIndex">
                  <option v-for="(item,index) in records" :key="recordId(item,index)" :value="index">{{ recordName(item) }} · {{ recordId(item,index) }}</option>
                </select>
              </div>
              <button class="btn btn-danger btn-sm" @click="requestDelete">{{ sectionMeta.deleteLabel }}</button>
            </section>

            <div v-if="hasRecordSection&&!records.length" class="web-empty-action">
              <strong>{{ sectionMeta.emptyTitle }}</strong>
              <p>{{ sectionMeta.emptyDescription }}</p>
              <button class="btn btn-primary" @click="addRecord">{{ sectionMeta.createLabel }}</button>
            </div>

            <template v-if="section==='pages'&&current">
              <div class="web-form-stack">
                <section class="web-form-section"><h3 class="web-form-title">基本信息</h3><div class="grid-2"><div class="form-row"><label class="label">页面 ID</label><input class="field" v-model.trim="current.page_id" placeholder="page.s3-building"></div><div class="form-row"><label class="label">显示名称</label><input class="field" v-model.trim="current.name" placeholder="楼宇总览"></div></div><label class="check-row"><input type="checkbox" v-model="current.enabled">启用页面</label></section>
                <section class="web-form-section"><h3 class="web-form-title">页面地址</h3><div class="form-row"><label class="label">基础 URL</label><input class="field" v-model.trim="current.base_url" placeholder="http://localhost:5000/ue_hud/pages/s3-building.html"><span class="hint">地址中的协议、账号信息与正式环境域名会在发布前校验。</span></div></section>
                <section class="web-form-section"><h3 class="web-form-title">上下文参数映射</h3><div class="grid-2"><div v-for="key in stableKeys" :key="key" class="form-row"><label class="label">{{ contextLabel(key) }}</label><input class="field" :value="current.param_mapping?.[key]||''" @input="setParamMapping(key,$event.target.value)" :placeholder="contextPlaceholder(key)"></div></div><div class="form-row web-extra-params"><label class="label">允许的额外参数</label><input class="field" :value="csv(current.declared_extra_params)" @change="current.declared_extra_params=parseCsv($event.target.value)" placeholder="event_id"><span class="hint">多个参数用英文逗号分隔；未声明的参数会被拒绝。</span></div></section>
                <section class="web-form-section"><h3 class="web-form-title">网页与场景联动</h3><div class="web-scope-effects"><div v-for="item in scopeTypes" :key="item.id" class="form-row"><label class="label">{{ item.label }}</label><select class="field" v-model="current.scope_effects[item.id]"><option value="web_only">只打开网页</option><option value="web_and_scene">网页与场景联动</option></select></div></div></section>
              </div>
            </template>

            <template v-else-if="section==='views'&&current">
              <div class="web-form-stack">
                <section class="web-form-section"><h3 class="web-form-title">基本信息</h3><div class="grid-2"><div class="form-row"><label class="label">业务管理 ID</label><input class="field" v-model.trim="current.business_view_id" placeholder="bv.fire"></div><div class="form-row"><label class="label">显示名称</label><input class="field" v-model.trim="current.name" placeholder="消防业务"></div></div><div class="form-row"><label class="label">说明</label><textarea class="field" v-model.trim="current.description"></textarea></div><label class="check-row"><input type="checkbox" v-model="current.enabled">启用业务管理</label></section>
                <section class="web-form-section">
                  <h3 class="web-form-title"><span>成员范围</span><button class="btn btn-sm" @click="addRuleGroup">添加另一组范围</button></h3>
                  <div class="web-rule-intro">
                    <strong>同一组内同时满足，多组之间满足任意一组即可。</strong>
                    <span>当前预计纳入 {{ businessMemberCount(current) }} 个实例。</span>
                  </div>
                  <template v-for="(group,index) in current.rule_groups" :key="index">
                    <div v-if="index" class="web-rule-connector"><span>或</span></div>
                    <div class="web-rule-card">
                      <div class="web-rule-head">
                        <div><strong>范围组 {{ index+1 }}</strong><span class="web-rule-match">{{ ruleGroupMatchCount(group) }} 个实例符合</span></div>
                        <button class="btn btn-ghost btn-sm" @click="current.rule_groups.splice(index,1)">移除这组</button>
                      </div>
                      <div class="web-rule-fields">
                        <div class="web-choice-row">
                          <div class="web-choice-copy"><strong>空间分区</strong><span>可多选；选择父级时自动包含下级分区</span></div>
                          <div class="web-choice-values">
                            <div v-if="group.zone_ids?.length" class="web-chip-list"><span v-for="id in group.zone_ids" :key="id" class="web-chip">{{ zoneLabel(id) }}<button type="button" @click="removeRuleSelection(group,'zone_ids',id)">移除</button></span></div>
                            <span v-else class="web-choice-empty">不限分区</span>
                          </div>
                          <button class="btn btn-sm" @click="openSelector('zone_ids',index)">选择分区</button>
                        </div>
                        <div class="web-choice-row">
                          <div class="web-choice-copy"><strong>设备类型</strong><span>同一类型下的实例会自动纳入</span></div>
                          <div class="web-choice-values">
                            <div v-if="group.object_type_rids?.length" class="web-chip-list"><span v-for="id in group.object_type_rids" :key="id" class="web-chip">{{ typeLabel(id) }}<button type="button" @click="removeRuleSelection(group,'object_type_rids',id)">移除</button></span></div>
                            <span v-else class="web-choice-empty">不限类型</span>
                          </div>
                          <button class="btn btn-sm" @click="openSelector('object_type_rids',index)">选择类型</button>
                        </div>
                        <div class="web-choice-row">
                          <div class="web-choice-copy"><strong>指定实例</strong><span>按上方条件缩小候选范围后再精确选择</span></div>
                          <div class="web-choice-values">
                            <div v-if="group.instance_ids?.length" class="web-chip-list"><span v-for="id in group.instance_ids" :key="id" class="web-chip">{{ instanceLabel(id) }}<button type="button" @click="removeRuleSelection(group,'instance_ids',id)">移除</button></span></div>
                            <span v-else class="web-choice-empty">不指定单个实例</span>
                          </div>
                          <button class="btn btn-sm" @click="openSelector('instance_ids',index)">选择实例</button>
                        </div>
                      </div>
                    </div>
                  </template>
                  <div v-if="!current.rule_groups.length" class="web-empty-action web-rule-empty">
                    <strong>还没有设置成员范围</strong>
                    <p>添加一组范围，再从分区、设备类型或具体实例中选择。至少选择一项才会匹配实例。</p>
                    <button class="btn btn-primary btn-sm" @click="addRuleGroup">添加第一组范围</button>
                  </div>
                </section>
                <section class="web-form-section">
                  <h3 class="web-form-title">排除实例</h3>
                  <p class="hint">排除项会在所有范围组合完成后统一移除。</p>
                  <div class="web-exclusion-picker">
                    <div v-if="current.exclude_instance_ids?.length" class="web-chip-list"><span v-for="id in current.exclude_instance_ids" :key="id" class="web-chip">{{ instanceLabel(id) }}<button type="button" @click="removeExclusion(id)">移除</button></span></div>
                    <span v-else class="web-choice-empty">当前没有排除项</span>
                    <button class="btn btn-sm" @click="openSelector('exclude_instance_ids',-1)">选择要排除的实例</button>
                  </div>
                </section>
              </div>
            </template>

            <template v-else-if="section==='bindings'&&current">
              <div class="web-form-stack">
                <section class="web-form-section"><h3 class="web-form-title">基本信息</h3><div class="grid-2"><div class="form-row"><label class="label">绑定 ID</label><input class="field" v-model.trim="current.binding_id" placeholder="bind.fire"></div><div class="form-row"><label class="label">显示名称</label><input class="field" v-model.trim="current.name" placeholder="消防业务主页"></div></div><label class="check-row"><input type="checkbox" v-model="current.enabled">启用绑定</label></section>
                <section class="web-form-section"><h3 class="web-form-title">触发与效果</h3><div class="grid-2"><div class="form-row"><label class="label">触发</label><select class="field" v-model="current.trigger"><option value="open_detail">打开对象详情</option><option value="project_home_activated">激活项目主页</option><option value="zone_activated">激活空间分区</option><option value="business_view_activated">激活业务管理</option></select></div><div class="form-row"><label class="label">激活方式</label><select class="field" v-model="current.activation_mode"><option value="explicit">明确点击</option><option value="direct">直接激活</option></select></div><div class="form-row"><label class="label">效果</label><select class="field" v-model="current.effect"><option value="open_web">打开页面</option><option value="block">阻止打开</option></select></div><div v-if="current.effect==='open_web'" class="form-row"><label class="label">页面</label><select class="field" v-model="current.page_id"><option value="">请选择</option><option v-for="page in draft.pages" :key="page.page_id" :value="page.page_id">{{ page.name||page.page_id }}</option></select></div></div></section>
                <section class="web-form-section"><h3 class="web-form-title">作用范围</h3><div class="grid-2"><div class="form-row"><label class="label">范围类型</label><select class="field" :value="scopeType(current.scope)" @change="changeScopeType($event.target.value)"><option value="project">项目默认</option><option value="zone">空间分区</option><option value="type">设备类型</option><option value="zone_type">空间分区 + 设备类型</option><option value="instance">实例</option><option value="business_view">业务管理</option></select></div><div v-if="scopeType(current.scope)==='zone'||scopeType(current.scope)==='zone_type'" class="form-row"><label class="label">分区 ID</label><input class="field" v-model.trim="current.scope.zone_id"></div><div v-if="scopeType(current.scope)==='type'||scopeType(current.scope)==='zone_type'" class="form-row"><label class="label">设备类型 ID</label><input class="field" v-model.trim="current.scope.object_type_rid"></div><div v-if="scopeType(current.scope)==='instance'" class="form-row"><label class="label">实例 ID</label><input class="field" v-model.trim="current.scope.instance_id"></div><div v-if="scopeType(current.scope)==='business_view'" class="form-row"><label class="label">业务管理</label><select class="field" v-model="current.scope.business_view_id"><option value="">请选择</option><option v-for="view in draft.business_views" :key="view.business_view_id" :value="view.business_view_id">{{ view.name||view.business_view_id }}</option></select></div></div></section>
              </div>
            </template>

            <template v-else-if="section==='preview'">
              <section class="web-form-section"><h3 class="web-form-title">模拟上下文</h3><div class="grid-2"><div class="form-row"><label class="label">触发</label><select class="field" v-model="previewForm.trigger"><option value="open_detail">打开对象详情</option><option value="project_home_activated">激活项目主页</option><option value="zone_activated">激活空间分区</option><option value="business_view_activated">激活业务管理</option></select></div><div class="form-row"><label class="label">实例 ID</label><input class="field" v-model.trim="previewForm.instance_id"></div><div class="form-row"><label class="label">分区 ID</label><input class="field" v-model.trim="previewForm.zone_id"></div><div class="form-row"><label class="label">设备类型 ID</label><input class="field" v-model.trim="previewForm.object_type_rid"></div><div class="form-row"><label class="label">业务管理 ID</label><input class="field" v-model.trim="previewForm.business_view_id"></div></div><div class="web-preview-action"><button class="btn btn-primary" :disabled="busy" @click="resolvePreview">{{ busy?'正在解析...':'运行解析' }}</button></div></section>
              <section v-if="previewResult" class="web-form-section"><h3 class="web-form-title">解析结果</h3><div v-if="previewResult.validation" class="web-status-list"><div v-for="item in previewResult.validation.errors" :key="item.path+item.code" class="web-status-item error">{{ displayPath(item.path) }} · {{ displayMessage(item.message) }}</div></div><template v-else><div class="web-status-item" :class="{warning:previewResult.result.blocked}">{{ previewResult.result.blocked?'已被规则阻止':(previewResult.result.binding?'命中 '+previewResult.result.binding.binding_id:'没有命中绑定') }}</div><div v-if="previewResult.result.final_url" class="web-status-item web-code">{{ previewResult.result.final_url }}</div><div class="web-chain"><div v-for="item in previewResult.result.chain" :key="item.level" class="web-chain-row" :class="item.result"><strong>{{ chainLevel(item.level) }}</strong><div class="row-meta">{{ chainResult(item) }}</div></div></div><div v-if="previewResult.result.scene_scope" class="notice">场景匹配 {{ previewResult.result.scene_scope.matched_instance_count }} 个实例；另有 {{ previewResult.result.scene_scope.unzoned_instance_count }} 个未分区实例保持常驻。</div></template></section>
            </template>

            <template v-else-if="section==='publish'">
              <section class="web-form-section"><h3 class="web-form-title">项目域名白名单</h3><div class="form-row"><label class="label">允许的域名</label><input class="field" :value="csv(draft.web_policy.allowed_hosts)" @change="draft.web_policy.allowed_hosts=parseCsv($event.target.value)" placeholder="localhost, example.com"><span class="hint">测试期开放模式仍会拒绝危险协议和地址内嵌账号；正式白名单模式按此列表校验。</span></div></section>
              <section class="web-form-section"><h3 class="web-form-title">配置摘要</h3><div class="web-summary"><div class="web-summary-card"><span class="web-summary-value">{{ draft.pages.length }}</span><span class="web-summary-label">页面资源</span></div><div class="web-summary-card"><span class="web-summary-value">{{ draft.business_views.length }}</span><span class="web-summary-label">业务管理</span></div><div class="web-summary-card"><span class="web-summary-value">{{ draft.bindings.length }}</span><span class="web-summary-label">页面绑定</span></div><div class="web-summary-card"><span class="web-summary-value">{{ revision }}</span><span class="web-summary-label">已发布版本</span></div></div></section>
              <section class="web-form-section"><h3 class="web-form-title"><span>发布校验</span><button class="btn btn-sm" :disabled="busy" @click="validateNow">重新校验</button></h3><div v-if="!validation" class="empty">尚未校验当前草稿。</div><div v-else class="web-status-list"><div v-if="validation.valid&&!validation.warnings.length" class="web-status-item">校验通过，可以发布。</div><div v-for="item in validation.errors" :key="item.path+item.code" class="web-status-item error">{{ displayPath(item.path) }} · {{ displayMessage(item.message) }}</div><div v-for="item in validation.warnings" :key="item.path+item.code" class="web-status-item warning">{{ displayMessage(item.message) }}</div></div></section>
              <section class="web-form-section"><h3 class="web-form-title">版本操作</h3><div class="web-publish-actions"><button class="btn btn-primary" :disabled="busy||dirty" @click="publish(false)">发布草稿</button><button class="btn" :disabled="busy||!hasPrevious" @click="requestRollback">回滚上一版本</button></div><p class="hint">发布前请先保存草稿。回滚会创建新的版本，不会把版本号减一。</p></section>
            </template>

            <div class="web-footer"><span class="hint">{{ dirty?'当前有未保存的草稿修改':'草稿已保存' }}</span><button class="btn btn-primary" :disabled="busy||!dirty" @click="saveDraft">{{ busy?'正在处理...':'保存草稿' }}</button></div>
          </div>
        </main>

        <aside class="web-inspector"><section class="section"><h2 class="section-title">状态与风险</h2><div class="web-status-list"><div v-if="!validation" class="web-status-item">保存或校验后，这里会显示发布风险。</div><template v-else><div v-if="validation.valid" class="web-status-item">结构校验通过</div><div v-for="item in validation.errors.slice(0,8)" :key="item.path+item.code" class="web-status-item error">{{ displayMessage(item.message) }}</div><div v-for="item in validation.warnings.slice(0,8)" :key="item.path+item.code" class="web-status-item warning">{{ displayMessage(item.message) }}</div></template></div></section><section class="section"><h2 class="section-title">固定规则</h2><div class="web-status-list"><div class="web-status-item">详情优先级<br>实例 → 分区+类型 → 类型 → 分区 → 项目</div><div class="web-status-item">业务管理优先级<br>业务管理 → 项目</div><div class="web-status-item">网页失败与场景失败相互独立，不自动回滚另一侧。</div></div></section></aside>

        <div v-if="selector.open" class="modal-mask" @click.self="closeSelector" @keydown.esc="closeSelector">
          <div class="modal web-selector-modal" role="dialog" aria-modal="true" :aria-label="selectorTitle">
            <h3>{{ selectorTitle }}</h3>
            <p class="web-selector-help">{{ selectorHelp }}</p>
            <input ref="selectorSearch" class="field" v-model.trim="selector.query" :placeholder="'搜索'+selectorItemName">
            <div class="web-selector-summary">已选 {{ selector.selected.length }} 项<span v-if="selector.kind==='instance_ids'&&selector.groupIndex>=0"> · 候选已按本组其他条件筛选</span></div>
            <div class="web-selector-options">
              <label v-for="option in selectorOptions" :key="option.id" class="web-selector-option" :class="{selected:selector.selected.includes(option.id)}">
                <input type="checkbox" :checked="selector.selected.includes(option.id)" @change="toggleSelectorValue(option.id)">
                <span class="web-selector-option-copy"><strong>{{ option.label }}</strong><span>{{ option.meta }}</span></span>
              </label>
              <div v-if="!selectorOptions.length" class="empty">没有符合当前搜索与筛选条件的选项。</div>
            </div>
            <div class="modal-foot"><button class="btn btn-ghost" @click="closeSelector">取消</button><button class="btn btn-primary" @click="applySelector">确认选择</button></div>
          </div>
        </div>

        <div v-if="dialog.open" class="modal-mask" @click.self="dialog.open=false"><div class="modal" role="dialog" aria-modal="true"><h3>{{ dialog.title }}</h3><p>{{ dialog.body }}</p><div class="modal-foot"><button class="btn btn-ghost" @click="dialog.open=false">取消</button><button class="btn btn-primary" @click="confirmDialog">{{ dialog.confirmText }}</button></div></div></div>
      </div>`,
    setup(props, { emit }) {
      const loading = ref(true), busy = ref(false), dirty = ref(false), hydrating = ref(false);
      const section = ref("pages"), selectedIndex = ref(0), revision = ref(0), hasPrevious = ref(false);
      const projectId = ref(""), projectName = ref(""), unzonedCount = ref(0), validation = ref(null), previewResult = ref(null);
      const zones = ref([]), objectTypes = ref([]), instances = ref([]);
      const draft = reactive(blankConfig());
      const previewForm = reactive({ trigger: "open_detail", instance_id: "", zone_id: "", object_type_rid: "", business_view_id: "" });
      const dialog = reactive({ open: false, title: "", body: "", confirmText: "确认", action: null });
      const selector = reactive({ open: false, kind: "", groupIndex: -1, query: "", selected: [] });
      const selectorSearch = ref(null);
      const scopeTypes = [{ id: "zone", label: "空间分区" }, { id: "business_view", label: "业务管理" }, { id: "instance", label: "实例" }];
      const records = computed(() => section.value === "pages" ? draft.pages : section.value === "views" ? draft.business_views : section.value === "bindings" ? draft.bindings : []);
      const current = computed(() => records.value[selectedIndex.value] || null);
      const hasRecordSection = computed(() => ["pages", "views", "bindings"].includes(section.value));
      const sectionMeta = computed(() => ({
        pages: { title: "页面资源", description: "注册可复用页面。绑定规则只能引用页面 ID，不能覆盖地址。", createLabel: "新建页面", selectionLabel: "当前页面", deleteLabel: "删除当前页面", emptyTitle: "还没有页面资源", emptyDescription: "先注册一个页面，再为它配置触发条件和发布规则。" },
        views: { title: "业务管理", description: "按空间、设备类型或指定实例组织业务范围。", createLabel: "新建业务", selectionLabel: "当前业务", deleteLabel: "删除当前业务", emptyTitle: "还没有业务配置", emptyDescription: "新建业务后，可用多个规则组组合需要管理的实例。" },
        bindings: { title: "页面绑定", description: "定义用户操作如何打开页面，或明确阻止当前范围打开页面。", createLabel: "新建绑定", selectionLabel: "当前绑定", deleteLabel: "删除当前绑定", emptyTitle: "还没有页面绑定", emptyDescription: "先选择触发方式、作用范围和要打开的页面。" },
        preview: { title: "解析预览", description: "使用当前草稿模拟一次触发，查看匹配顺序、最终地址和场景范围。" },
        publish: { title: "发布与回滚", description: "保存草稿不会影响三维端；发布整套配置后版本号才会增加。" },
      })[section.value]);
      const sections = computed(() => [
        { id: "pages", label: "页面资源", count: draft.pages.length },
        { id: "views", label: "业务管理", count: draft.business_views.length },
        { id: "bindings", label: "页面绑定", count: draft.bindings.length },
        { id: "preview", label: "解析预览", count: null },
        { id: "publish", label: "发布与回滚", count: null },
      ]);
      const selectorItemName = computed(() => ({ zone_ids: "分区", object_type_rids: "设备类型", instance_ids: "实例", exclude_instance_ids: "实例" })[selector.kind] || "选项");
      const selectorTitle = computed(() => selector.kind === "exclude_instance_ids" ? "选择要排除的实例" : `选择${selectorItemName.value}`);
      const selectorHelp = computed(() => ({
        zone_ids: "勾选一个或多个空间分区。选择父级分区时，会自动包含它的下级分区。",
        object_type_rids: "勾选一个或多个设备类型。所选类型中的实例将参与本组匹配。",
        instance_ids: "勾选需要精确限定的实例；候选列表已按本组分区和设备类型缩小。",
        exclude_instance_ids: "勾选不应出现在当前业务中的实例。排除规则最后执行。",
      })[selector.kind] || "");
      const selectorOptions = computed(() => {
        const query = selector.query.toLocaleLowerCase();
        let options = [];
        if (selector.kind === "zone_ids") {
          options = zones.value.map(zone => ({
            id: zone.id,
            label: `${"— ".repeat(zoneDepth(zone))}${zone.name || "未命名分区"}`,
            meta: `${zoneLevelLabel(zone.level)} · ${Number(zone.instance_count || 0)} 个实例`,
            search: `${zone.name || ""} ${zone.id || ""} ${zone.level || ""}`,
          }));
        } else if (selector.kind === "object_type_rids") {
          options = objectTypes.value.map(type => ({
            id: type.rid,
            label: type.name || "未命名类型",
            meta: `${type.category || "设备类型"} · ${instances.value.filter(item => item.object_type_rid === type.rid).length} 个实例`,
            search: `${type.name || ""} ${type.rid || ""} ${type.category || ""}`,
          }));
        } else if (selector.kind === "instance_ids" || selector.kind === "exclude_instance_ids") {
          let source = instances.value;
          if (selector.kind === "instance_ids" && selector.groupIndex >= 0) {
            const group = current.value?.rule_groups?.[selector.groupIndex] || {};
            const allowedZones = expandedZoneIds(group.zone_ids || []);
            source = source.filter(item =>
              (!group.zone_ids?.length || allowedZones.has(item.zone_id)) &&
              (!group.object_type_rids?.length || group.object_type_rids.includes(item.object_type_rid)) ||
              selector.selected.includes(item.id)
            );
          }
          options = source.map(item => ({
            id: item.id,
            label: item.display_name || item.name || "未命名实例",
            meta: `${item.object_type_name || typeLabel(item.object_type_rid)} · ${zoneLabel(item.zone_id)}`,
            search: `${item.display_name || ""} ${item.name || ""} ${item.id || ""} ${item.object_type_name || ""} ${zoneLabel(item.zone_id)}`,
          }));
        }
        const knownIds = new Set(options.map(option => option.id));
        selector.selected.filter(id => !knownIds.has(id)).forEach(id => options.unshift({
          id,
          label: `已失效：${id}`,
          meta: "当前项目中找不到这一项，可取消勾选后重新选择",
          search: id,
        }));
        return options.filter(option => !query || `${option.label} ${option.meta} ${option.search}`.toLocaleLowerCase().includes(query));
      });
      const notify = (message, type = "") => emit("toast", message, type);
      function assignDraft(value) {
        hydrating.value = true;
        const next = value || blankConfig();
        draft.pages.splice(0, draft.pages.length, ...clone(next.pages || []));
        draft.business_views.splice(0, draft.business_views.length, ...clone(next.business_views || []));
        draft.bindings.splice(0, draft.bindings.length, ...clone(next.bindings || []));
        draft.web_policy = clone(next.web_policy || { allowed_hosts: [] });
        dirty.value = false; emit("dirty-change", false);
        setTimeout(() => { hydrating.value = false; }, 0);
      }
      async function load() {
        loading.value = true;
        try {
          const [configRes, zoneRes, typeRes, instanceRes] = await Promise.all([
            axios.get("/api/v2/web-interactions"),
            axios.get("/api/v2/zones"),
            axios.get("/api/v2/ontology/types"),
            axios.get("/api/v2/instances"),
          ]);
          const data = configRes.data;
          projectId.value = data.project_id; projectName.value = data.project_name; revision.value = Number(data.revision || 0); hasPrevious.value = !!data.has_previous_published;
          zones.value = zoneRes.data.zones || []; objectTypes.value = typeRes.data || []; instances.value = instanceRes.data || [];
          unzonedCount.value = Number(zoneRes.data.unassigned_count || 0); validation.value = data.draft_validation || null;
          assignDraft(data.draft);
        } catch (error) { notify(error.response?.data?.message || "页面交互工作台加载失败", "err"); }
        finally { loading.value = false; }
      }
      watch(draft, () => { if (!hydrating.value) { dirty.value = true; emit("dirty-change", true); } }, { deep: true });
      function selectSection(value) { section.value = value; selectedIndex.value = 0; }
      function recordId(item, index) { return item?.page_id || item?.business_view_id || item?.binding_id || `未命名 ${index + 1}`; }
      function recordName(item) { return item?.name || recordId(item, 0); }
      function addRecord() {
        if (section.value === "pages") draft.pages.push({ page_id: "", name: "", enabled: true, base_url: "", param_mapping: {}, declared_extra_params: [], scope_effects: { zone: "web_only", business_view: "web_only", instance: "web_only" } });
        if (section.value === "views") draft.business_views.push({ business_view_id: "", name: "", description: "", enabled: true, rule_groups: [], exclude_instance_ids: [] });
        if (section.value === "bindings") draft.bindings.push({ binding_id: "", name: "", enabled: true, trigger: "open_detail", activation_mode: "explicit", effect: "open_web", scope: {}, page_id: "" });
        selectedIndex.value = records.value.length - 1;
      }
      function ask(title, body, confirmText, action) { Object.assign(dialog, { open: true, title, body, confirmText, action }); }
      function confirmDialog() { const action = dialog.action; dialog.open = false; dialog.action = null; if (typeof action === "function") action(); }
      function requestDelete() { ask("删除当前配置", `将删除“${recordName(current.value)}”。保存草稿前仍可刷新页面恢复。`, "确认删除", () => { records.value.splice(selectedIndex.value, 1); selectedIndex.value = Math.max(0, selectedIndex.value - 1); }); }
      function addRuleGroup() { current.value.rule_groups.push({ zone_ids: [], object_type_rids: [], instance_ids: [] }); }
      function zoneDepth(zone) {
        let depth = 0, parentId = zone?.parent_zone_id, guard = 0;
        while (parentId && guard < zones.value.length) {
          depth += 1; parentId = zones.value.find(item => item.id === parentId)?.parent_zone_id; guard += 1;
        }
        return depth;
      }
      function zoneLevelLabel(level) { return ({ building: "楼宇", floor: "楼层", area: "区域", room: "房间" })[level] || "空间分区"; }
      function zoneLabel(id) { return zones.value.find(item => item.id === id)?.name || (id ? `未找到的分区（${id}）` : "未分区"); }
      function typeLabel(id) { return objectTypes.value.find(item => item.rid === id)?.name || (id ? `未找到的类型（${id}）` : "未指定类型"); }
      function instanceLabel(id) {
        const item = instances.value.find(instance => instance.id === id);
        return item?.display_name || item?.name || (id ? `未找到的实例（${id}）` : "未命名实例");
      }
      function expandedZoneIds(zoneIds) {
        const result = new Set(zoneIds || []);
        let changed = true;
        while (changed) {
          changed = false;
          zones.value.forEach(zone => {
            if (zone.parent_zone_id && result.has(zone.parent_zone_id) && !result.has(zone.id)) {
              result.add(zone.id); changed = true;
            }
          });
        }
        return result;
      }
      function ruleGroupMatches(group) {
        if (!["zone_ids", "object_type_rids", "instance_ids"].some(key => group?.[key]?.length)) return [];
        const allowedZones = expandedZoneIds(group.zone_ids || []);
        return instances.value.filter(item =>
          (!group.zone_ids?.length || allowedZones.has(item.zone_id)) &&
          (!group.object_type_rids?.length || group.object_type_rids.includes(item.object_type_rid)) &&
          (!group.instance_ids?.length || group.instance_ids.includes(item.id))
        );
      }
      function ruleGroupMatchCount(group) { return ruleGroupMatches(group).length; }
      function businessMemberCount(view) {
        const included = new Set();
        (view?.rule_groups || []).forEach(group => ruleGroupMatches(group).forEach(item => included.add(item.id)));
        (view?.exclude_instance_ids || []).forEach(id => included.delete(id));
        return included.size;
      }
      function openSelector(kind, groupIndex) {
        const source = kind === "exclude_instance_ids"
          ? (current.value?.exclude_instance_ids || [])
          : (current.value?.rule_groups?.[groupIndex]?.[kind] || []);
        Object.assign(selector, { open: true, kind, groupIndex, query: "", selected: [...source] });
        nextTick(() => selectorSearch.value?.focus());
      }
      function closeSelector() { selector.open = false; selector.query = ""; }
      function toggleSelectorValue(id) {
        const index = selector.selected.indexOf(id);
        if (index >= 0) selector.selected.splice(index, 1); else selector.selected.push(id);
      }
      function applySelector() {
        if (selector.kind === "exclude_instance_ids") {
          current.value.exclude_instance_ids = [...selector.selected];
        } else {
          const group = current.value?.rule_groups?.[selector.groupIndex];
          if (group) group[selector.kind] = [...selector.selected];
        }
        closeSelector();
      }
      function removeRuleSelection(group, key, id) { group[key] = (group[key] || []).filter(item => item !== id); }
      function removeExclusion(id) { current.value.exclude_instance_ids = (current.value.exclude_instance_ids || []).filter(item => item !== id); }
      function setParamMapping(key, value) { if (!current.value.param_mapping) current.value.param_mapping = {}; const cleaned = String(value || "").trim(); if (cleaned) current.value.param_mapping[key] = cleaned; else delete current.value.param_mapping[key]; }
      function contextLabel(key) { return ({ project_id: "项目 ID", business_view_id: "业务管理 ID", zone_id: "分区 ID", object_type_rid: "设备类型 ID", instance_id: "实例 ID", trigger: "触发来源" })[key] || key; }
      function contextPlaceholder(key) { return ({ project_id: "project_id", business_view_id: "business_id", zone_id: "space_id", object_type_rid: "type_id", instance_id: "instance_id", trigger: "trigger" })[key] || key; }
      function displayPath(path) { return String(path || "").replaceAll("business_views", "业务管理").replaceAll("business_view_id", "业务管理 ID").replaceAll("object_type_rid", "设备类型 ID").replaceAll("zone_id", "分区 ID"); }
      function displayMessage(message) { return String(message || "").replace(/BusinessView/gi, "业务管理").replaceAll("业务视图", "业务管理"); }
      function chainLevel(level) { return ({ Instance: "实例", "Zone+Type": "分区+类型", Type: "类型", Zone: "分区", Project: "项目", BusinessView: "业务管理" })[level] || displayMessage(level); }
      function scopeType(scope) { if (scope?.instance_id) return "instance"; if (scope?.business_view_id) return "business_view"; if (scope?.zone_id && scope?.object_type_rid) return "zone_type"; if (scope?.object_type_rid) return "type"; if (scope?.zone_id) return "zone"; return "project"; }
      function changeScopeType(type) { current.value.scope = type === "zone" ? { zone_id: "" } : type === "type" ? { object_type_rid: "" } : type === "zone_type" ? { zone_id: "", object_type_rid: "" } : type === "instance" ? { instance_id: "" } : type === "business_view" ? { business_view_id: "" } : {}; }
      async function saveDraft() {
        busy.value = true;
        try { const res = await axios.put("/api/v2/web-interactions/draft", { expected_revision: revision.value, draft: clone(draft) }); validation.value = res.data.validation; assignDraft(res.data.draft); notify("草稿已保存", "ok"); }
        catch (error) { notify(error.response?.data?.message || "草稿保存失败", "err"); }
        finally { busy.value = false; }
      }
      async function validateNow() {
        busy.value = true;
        try { const res = await axios.post("/api/v2/web-interactions/validate", { config: clone(draft) }); validation.value = res.data; notify(res.data.valid ? "校验完成" : "发现需要修正的问题", res.data.valid ? "ok" : "err"); }
        catch (error) { notify(error.response?.data?.message || "校验失败", "err"); }
        finally { busy.value = false; }
      }
      async function publish(confirmWarnings) {
        busy.value = true;
        try {
          const res = await axios.post("/api/v2/web-interactions/publish", { expected_revision: revision.value, confirm_warnings: !!confirmWarnings });
          if (res.data.status === "validation_failed") { validation.value = res.data; notify("发布前仍有硬错误", "err"); return; }
          if (res.data.status === "warning_confirmation_required") { validation.value = res.data; ask("确认带警告发布", res.data.warnings.map(item => item.message).join("；"), "继续发布", () => publish(true)); return; }
          revision.value = Number(res.data.revision); hasPrevious.value = true; dirty.value = false; emit("dirty-change", false); notify(`已发布 revision ${revision.value}`, "ok"); await load();
        } catch (error) { notify(error.response?.data?.message || "发布失败", "err"); }
        finally { busy.value = false; }
      }
      function requestRollback() { ask("回滚上一已发布版本", "回滚会把上一快照重新发布为新的 revision，当前版本仍保留为可再次回滚的上一版本。", "确认回滚", rollback); }
      async function rollback() { busy.value = true; try { const res = await axios.post("/api/v2/web-interactions/rollback", { expected_revision: revision.value }); revision.value = Number(res.data.revision); notify(`已回滚并生成 revision ${revision.value}`, "ok"); await load(); } catch (error) { notify(error.response?.data?.message || "回滚失败", "err"); } finally { busy.value = false; } }
      async function resolvePreview() {
        busy.value = true; previewResult.value = null;
        try { const context = {}; ["instance_id", "zone_id", "object_type_rid", "business_view_id"].forEach(key => { if (previewForm[key]) context[key] = previewForm[key]; }); const res = await axios.post("/api/v2/web-interactions/resolve-preview", { trigger: previewForm.trigger, context, config: clone(draft) }); previewResult.value = res.data; }
        catch (error) { notify(error.response?.data?.message || "解析预览失败", "err"); }
        finally { busy.value = false; }
      }
      function chainResult(item) { return ({ context_missing: "当前上下文缺少该层级需要的 ID", no_binding: "无绑定，继续回退", disabled: "绑定已禁用，继续回退", matched: `命中 ${item.binding_id}`, blocked: `由 ${item.binding_id} 阻止` })[item.result] || item.result; }
      onMounted(load);
      return { loading, busy, dirty, section, selectedIndex, revision, hasPrevious, projectId, projectName, unzonedCount, validation, previewResult, previewForm, draft, dialog, selector, selectorSearch, selectorItemName, selectorTitle, selectorHelp, selectorOptions, stableKeys, scopeTypes, sections, sectionMeta, hasRecordSection, records, current, csv, parseCsv, selectSection, recordId, recordName, addRecord, requestDelete, addRuleGroup, zoneLabel, typeLabel, instanceLabel, ruleGroupMatchCount, businessMemberCount, openSelector, closeSelector, toggleSelectorValue, applySelector, removeRuleSelection, removeExclusion, setParamMapping, contextLabel, contextPlaceholder, displayPath, displayMessage, chainLevel, scopeType, changeScopeType, saveDraft, validateNow, publish, requestRollback, resolvePreview, chainResult, confirmDialog };
    }
  };
})(window);
