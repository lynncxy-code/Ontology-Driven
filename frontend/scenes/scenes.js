const API_BASE = '/api/v3/lite';

const api = {
    scenes: {
        list:   ()       => axios.get(`${API_BASE}/scenes`),
        create: (data)   => axios.post(`${API_BASE}/scenes`, data),
        get:    (id)     => axios.get(`${API_BASE}/scenes/${id}`),
        export: (id, opts) => axios.post(`${API_BASE}/scenes/${id}/export`, opts),
        removeInstance: (sceneId, instId) =>
            axios.delete(`${API_BASE}/scenes/${sceneId}/instances/${instId}`),
        addInstances: (sceneId, ids) =>
            axios.post(`${API_BASE}/scenes/${sceneId}/instances`, { instance_ids: ids }),
    },
    instances: {
        list:   () => axios.get(`${API_BASE}/instances`),
        create: (data) => axios.post(`${API_BASE}/instances`, data),
    },
    assets: {
        list: () => axios.get(`${API_BASE}/assets`),
    },
};

const { createApp } = Vue;

createApp({
    data() {
        return {
            scenes:        [],
            selectedScene: null,
            sceneInstances: [],
            assets:        [],
            allInstances:  [],

            exporting:    false,
            exportResult: null,

            showCreateScene:  false,
            newScene: {
                id: '', display_name: '',
                bounds_x_min: -3, bounds_x_max: 3,
                bounds_y_min: -3, bounds_y_max: 3,
                bounds_z_min:  0, bounds_z_max: 3,
            },

            showAddInstance: false,
            addInst: { instance_id: '' },

            showQuickAdd:   false,
            quickAddAsset:  null,
            quickAddForm:   { id: '', display_name: '', tx: 0, ty: 0, tz: 0, collision_type: 'static' },
        };
    },

    computed: {
        // instances not yet in the current scene
        availableInstances() {
            if (!this.selectedScene) return this.allInstances;
            const inScene = new Set((this.selectedScene.instance_ids || []));
            return this.allInstances.filter(i => !inScene.has(i.id));
        },
    },

    methods: {
        fmt3(arr) {
            return `[${arr.map(v => Number(v).toFixed(2)).join(', ')}]`;
        },

        // ── Scene list ──────────────────────────────────────────
        async loadScenes() {
            const { data } = await api.scenes.list();
            this.scenes = data.items || [];
        },

        async selectScene(id) {
            this.exportResult = null;
            const { data } = await api.scenes.get(id);
            this.selectedScene = data;
            await this.loadSceneInstances();
        },

        async loadSceneInstances() {
            if (!this.selectedScene) return;
            const ids = this.selectedScene.instance_ids || [];
            const all = await api.instances.list();
            const allMap = Object.fromEntries((all.data.items || []).map(i => [i.id, i]));
            this.sceneInstances = ids.map(id => allMap[id]).filter(Boolean);
        },

        async createScene() {
            if (!this.newScene.id || !this.newScene.display_name) {
                alert('请填写场景 ID 和显示名称');
                return;
            }
            const s = this.newScene;
            await api.scenes.create({
                id: s.id,
                display_name: s.display_name,
                bounds: {
                    x: [s.bounds_x_min, s.bounds_x_max],
                    y: [s.bounds_y_min, s.bounds_y_max],
                    z: [s.bounds_z_min, s.bounds_z_max],
                },
            });
            this.showCreateScene = false;
            this.newScene = { id: '', display_name: '',
                bounds_x_min: -3, bounds_x_max: 3,
                bounds_y_min: -3, bounds_y_max: 3,
                bounds_z_min:  0, bounds_z_max: 3 };
            await this.loadScenes();
        },

        // ── Export ──────────────────────────────────────────────
        async exportScene() {
            if (!this.selectedScene) return;
            this.exporting    = true;
            this.exportResult = null;
            try {
                const { data } = await api.scenes.export(this.selectedScene.id, { include_physics: true });
                this.exportResult = data;
            } catch (err) {
                const msg = err.response?.data?.error?.message || err.message;
                this.exportResult = { error: `导出失败：${msg}` };
            } finally {
                this.exporting = false;
            }
        },

        // ── Instances ───────────────────────────────────────────
        async removeInstance(instId) {
            if (!this.selectedScene) return;
            await api.scenes.removeInstance(this.selectedScene.id, instId);
            await this.selectScene(this.selectedScene.id);
        },

        async addInstanceToScene() {
            if (!this.addInst.instance_id) return;
            await api.scenes.addInstances(this.selectedScene.id, [this.addInst.instance_id]);
            this.showAddInstance   = false;
            this.addInst.instance_id = '';
            await this.selectScene(this.selectedScene.id);
        },

        // ── Quick Add (from asset library) ──────────────────────
        quickAddInstance(asset) {
            this.quickAddAsset = asset;
            this.quickAddForm  = {
                id:             asset.file_number + '_' + String(Date.now()).slice(-4),
                display_name:   asset.display_name,
                tx: 0, ty: 0, tz: 0,
                collision_type: 'static',
            };
            this.showQuickAdd = true;
        },

        async submitQuickAdd() {
            const a = this.quickAddAsset;
            const f = this.quickAddForm;
            if (!f.id) { alert('请填写实例 ID'); return; }

            try {
                await api.instances.create({
                    id:              f.id,
                    object_type_rid: a.file_number,
                    file_number:     a.file_number,
                    display_name:    f.display_name || a.display_name,
                    transform: {
                        translation: [f.tx, f.ty, f.tz],
                        rotation:    [0, 0, 0],
                        scale:       [1, 1, 1],
                    },
                    physics: {
                        collision_type: f.collision_type,
                    },
                });
                await api.scenes.addInstances(this.selectedScene.id, [f.id]);
                this.showQuickAdd = false;
                await this.selectScene(this.selectedScene.id);
            } catch (err) {
                alert('创建失败：' + (err.response?.data?.error?.message || err.message));
            }
        },

        // ── Assets ──────────────────────────────────────────────
        async loadAssets() {
            const { data } = await api.assets.list();
            this.assets = data.items || [];
        },

        async loadAllInstances() {
            const { data } = await api.instances.list();
            this.allInstances = data.items || [];
        },
    },

    async mounted() {
        await Promise.all([this.loadScenes(), this.loadAssets(), this.loadAllInstances()]);
        // auto-select first scene if any
        if (this.scenes.length > 0) {
            await this.selectScene(this.scenes[0].id);
        }
    },
}).mount('#app');
