window.SceneryNumberBinding = {
    props: { instance: Object, projectId: String, disabled: Boolean },
    emits: ['bound'],
    data() {
        return { options: null, loading: false, saving: false, message: '', mode: 'roster',
            number: '', typeRid: '', expectedProject: '' };
    },
    computed: {
        endpoint() { return '/api/v2/instances/' + encodeURIComponent(this.instance.id) + '/business-number'; },
        rosterType() {
            if (this.mode !== 'roster') return null;
            const hint = this.options?.roster.find(r => r.instance_id === this.number)?.type;
            return this.options?.types.find(t => t.rid === hint || t.name === hint);
        },
        effectiveType() { return this.rosterType?.rid || this.typeRid; },
    },
    methods: {
        async open() {
            this.expectedProject = this.projectId;
            this.options = null;
            this.loading = true;
            this.setMode('roster');
            this.$refs.dialog.showModal();
            try {
                const {data} = await axios.get(this.endpoint);
                if (data.project_id !== this.expectedProject) throw new Error('数据集已切换，请刷新实例页面');
                this.options = data;
                if (!data.roster.length) this.setMode('new');
                if (!data.types.length) this.message = '请先为业务类型启用三维表现和空间能力。';
            } catch (error) {
                this.message = error.response?.data?.message || error.message || '读取待投产清单失败';
            } finally {
                this.loading = false;
            }
        },
        setMode(mode) {
            this.mode = mode;
            this.number = '';
            this.typeRid = '';
            this.message = '';
        },
        async save() {
            if (this.saving || !this.number.trim() || !this.effectiveType) return;
            this.message = '';
            this.saving = true;
            try {
                const {data} = await axios.post(this.endpoint, {
                    mode: this.mode, instance_id: this.number.trim(), object_type_rid: this.effectiveType,
                    expected_project_id: this.expectedProject,
                });
                this.$refs.dialog?.close();
                this.$emit('bound', data.instance_id);
            } catch (error) {
                this.message = error.response?.data?.message || '未能确认绑定结果，请刷新实例列表后重试。';
            } finally {
                this.saving = false;
            }
        },
    },
    template: `
        <button type="button" class="ic-btn" :disabled="disabled || !projectId || loading" @click="open">绑定业务编号</button>
        <teleport to="body">
            <dialog ref="dialog" class="il-spawn-dialog il-number-dialog" aria-labelledby="bind-number-title"
                    @cancel="saving && $event.preventDefault()">
                <form @submit.prevent="save">
                    <header class="il-spawn-head">
                        <h2 id="bind-number-title">绑定业务编号</h2>
                        <p>{{ instance.display_name }} · 场景陈设</p>
                    </header>
                    <fieldset class="il-spawn-fields space-y-3" :disabled="saving || loading">
                        <p v-if="loading" role="status">正在读取待投产清单…</p>
                        <template v-if="options">
                            <div class="flex gap-4">
                                <label><input type="radio" name="number-mode" :checked="mode === 'roster'" @change="setMode('roster')"> 从待投产清单选</label>
                                <label><input type="radio" name="number-mode" :checked="mode === 'new'" @change="setMode('new')"> 填写新编号</label>
                            </div>
                            <label class="block">业务编号
                                <select v-if="mode === 'roster'" aria-label="业务编号" v-model="number" @change="typeRid = ''; message = ''">
                                    <option disabled value="">{{ options.roster.length ? '请选择待投产编号' : '暂无待投产编号' }}</option>
                                    <option v-for="r in options.roster" :value="r.instance_id" :key="r.instance_id">{{ r.instance_id }}{{ r.name ? ' · ' + r.name : '' }}</option>
                                </select>
                                <input v-else type="text" aria-label="业务编号" v-model.trim="number" maxlength="255" placeholder="输入新业务编号" @input="message = ''">
                            </label>
                            <label class="block">业务类型
                                <select aria-label="业务类型" :value="effectiveType" :disabled="!!rosterType" @change="typeRid = $event.target.value; message = ''">
                                    <option disabled value="">请选择业务类型</option>
                                    <option v-for="t in options.types" :key="t.rid" :value="t.rid">{{ t.name }}</option>
                                </select>
                            </label>
                        </template>
                    </fieldset>
                    <footer class="il-spawn-foot">
                        <p v-if="message" role="alert" class="ic-error">{{ message }}</p>
                        <div class="ic-actions">
                            <button type="button" class="ic-btn" :disabled="saving" @click="$refs.dialog.close()">取消</button>
                            <button class="ic-btn ic-btn-primary" :disabled="!options || !number || !effectiveType || saving">{{ saving ? '正在绑定…' : '确认绑定' }}</button>
                        </div>
                    </footer>
                </form>
            </dialog>
        </teleport>`,
};
