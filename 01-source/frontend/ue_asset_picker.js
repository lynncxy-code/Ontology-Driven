/* Shared, build-free Vue picker for the active project's UE catalog. */
(function (root) {
  'use strict';
  const kinds = {StaticMesh:'静态网格体', SkeletalMesh:'骨骼网格体', Blueprint:'蓝图'};
  const kindLabel = kind => kinds[kind] || '其他模型';
  const projectId = ds => ds?.project_id || ds?.id || '';
  const normalizeFolder = path => String(path || '').replace(/\\/g,'/').replace(/\/+$/,'');
  const assetFolder = asset => normalizeFolder(asset.folder_path || asset.object_path?.slice(0,asset.object_path.lastIndexOf('/')));
  const insideFolder = (path, parent) => path === parent || path.startsWith(parent+'/');
  const folderLabel = path => path === '/Game' ? 'Content' : path.split('/').pop();
  function buildFolders(catalog) {
    const nodes=new Map();
    function add(path) {
      path=normalizeFolder(path);
      if(!path.startsWith('/') || path==='')return;
      const parts=path.split('/').filter(Boolean);
      for(let i=1;i<=parts.length;i++){
        const key='/'+parts.slice(0,i).join('/');
        if(!nodes.has(key))nodes.set(key,{path:key,parent:i===1?'':'/'+parts.slice(0,i-1).join('/'),
          label:folderLabel(key),depth:i-1,children:[],count:0});
      }
    }
    [...(catalog?.available_folders || []),...(catalog?.roots || [])].forEach(add);
    for(const asset of catalog?.assets || []){
      let path=assetFolder(asset);add(path);
      while(path){const node=nodes.get(path);if(node)node.count++;path=path.slice(0,path.lastIndexOf('/'));}
    }
    const roots=[];
    for(const node of nodes.values()){
      if(node.parent)nodes.get(node.parent)?.children.push(node);else roots.push(node);
    }
    const sort=list=>{list.sort((a,b)=>a.label.localeCompare(b.label,'zh-CN',{numeric:true}));list.forEach(n=>sort(n.children));};
    sort(roots);
    return {nodes,roots};
  }
  function filterAssets(assets, folder, descendants, kind, query) {
    const text=query.trim().toLowerCase();
    return assets.filter(a=>(descendants?insideFolder(assetFolder(a),folder):assetFolder(a)===folder) &&
      (!kind || a.asset_kind===kind) &&
      `${a.display_name || ''} ${a.asset_name || ''} ${a.object_path || ''}`.toLowerCase().includes(text))
      .sort((a,b)=>(a.display_name || a.asset_name || '').localeCompare(b.display_name || b.asset_name || '', 'zh-CN',{numeric:true}));
  }
  function selection(asset, catalog, dataset) {
    return {
      file_number:asset.object_path, ue_path:asset.object_path,
      name:asset.display_name || asset.asset_name, bindable:asset.runtime_supported === true,
      source:'ue_catalog', expected_project_id:projectId(dataset),
      ue_project_id:catalog.ue_project_id, catalog_revision:catalog.catalog_revision,
      asset_kind:asset.asset_kind
    };
  }
  const component = {
    props:{dataset:Object, disabled:Boolean},
    emits:['select'],
    setup(props, {emit}) {
      const {ref, computed, watch, onUnmounted} = Vue;
      const catalog=ref(null), loading=ref(false), scanning=ref(false), error=ref(''), notice=ref('');
      const folder=ref(''), query=ref(''), kind=ref(''), page=ref(1), selected=ref('');
      const descendants=ref(false), expanded=ref(new Set());
      let sequence=0, timer=null;
      const context=()=>JSON.stringify([projectId(props.dataset),props.dataset?.bound_ue_project_id]);
      const clearSelection=()=>{selected.value='';emit('select',null);};
      const stop=()=>{clearTimeout(timer);timer=null;scanning.value=false;};
      const directories=computed(()=>buildFolders(catalog.value));
      const treeRows=computed(()=>{
        const rows=[];
        function visit(nodes){for(const node of nodes){rows.push(node);if(expanded.value.has(node.path))visit(node.children);}}
        visit(directories.value.roots);return rows;
      });
      const subfolders=computed(()=>directories.value.nodes.get(folder.value)?.children || []);
      const breadcrumbs=computed(()=>folder.value.split('/').filter(Boolean).map((_,i,parts)=>{
        const path='/'+parts.slice(0,i+1).join('/');return {path,label:folderLabel(path)};
      }));
      const covered=computed(()=>(catalog.value?.roots || []).some(root=>insideFolder(folder.value,normalizeFolder(root))));
      const filtered=computed(()=>filterAssets(catalog.value?.assets || [],folder.value,descendants.value,kind.value,query.value));
      const pages=computed(()=>Math.max(1,Math.ceil(filtered.value.length/24)));
      const items=computed(()=>filtered.value.slice((page.value-1)*24,page.value*24));
      watch([query,kind,descendants],()=>{page.value=1;clearSelection();});
      function openFolder(path) {
        folder.value=path;page.value=1;clearSelection();
        const next=new Set(expanded.value);
        let ancestor=path;
        while(ancestor){next.add(ancestor);ancestor=ancestor.slice(0,ancestor.lastIndexOf('/'));}
        expanded.value=next;
      }
      function toggleFolder(path){
        const next=new Set(expanded.value);next.has(path)?next.delete(path):next.add(path);expanded.value=next;
      }
      const stamp=value=>value ? new Date(value).toLocaleString('zh-CN') : '尚未同步';
      const reason=asset=>asset.runtime_supported ? '' :
        (asset.runtime_reason?.includes('重新同步') ? '请重新同步以确认此蓝图是否可用' : '当前模型类型或蓝图生成类暂不支持绑定');
      async function request(url, options) {
        const response=await fetch(url,options);
        const data=await response.json();
        if(!response.ok)throw new Error(data.message || '读取失败，请稍后重试。');
        return data;
      }
      async function checkContext() {
        const datasets=await request('/api/v2/ontology/datasets');
        const active=datasets.find(ds=>ds.is_active);
        if(projectId(active)!==projectId(props.dataset) ||
          active?.bound_ue_project_id!==props.dataset?.bound_ue_project_id)
          throw new Error('当前项目或绑定工程已变化，请刷新页面后重新选择。');
      }
      async function load() {
        const token=++sequence, key=context();
        stop();clearSelection();error.value='';notice.value='';loading.value=true;
        const ue=props.dataset?.bound_ue_project_id;
        if(!ue){catalog.value=null;loading.value=false;return;}
        try {
          await checkContext();
          const data=await request('/api/v2/ue/assets/catalog?ue_project_id='+encodeURIComponent(ue));
          if(token!==sequence || key!==context())return;
          if(data.ue_project_id!==ue)throw new Error('返回的资产清单不属于当前绑定工程。');
          catalog.value=data;
          openFolder(directories.value.nodes.has(folder.value)?folder.value:(data.roots?.[0] || directories.value.roots[0]?.path || ''));
          notice.value='显示上次同步清单。新增模型请先在 UE 导入，再更新对应目录。';
        } catch(e) {if(token===sequence){catalog.value=null;error.value=e.message;}}
        finally {if(token===sequence)loading.value=false;}
      }
      async function scan() {
        if(scanning.value || loading.value || props.disabled)return;
        const path=folder.value.trim().replace(/\/+$/,'');
        if(!/^\/Game(?:\/[^.]+)?$/.test(path)){error.value='请选择 /Game 或其子目录，不要填写具体模型路径。';return;}
        const token=++sequence,key=context(),ue=props.dataset.bound_ue_project_id;
        stop();clearSelection();error.value='';scanning.value=true;
        notice.value='正在请求 UE 扫描所选目录及子目录…';
        try {
          await checkContext();
          if(token!==sequence || key!==context())return;
          const result=await request('/api/v2/ue/assets/scan-requests',{
            method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ue_project_id:ue,folder_path:path,expected_project_id:projectId(props.dataset)})
          });
          if(token!==sequence || key!==context())return;
          const started=Date.now();
          const poll=async()=>{
            if(token!==sequence || key!==context())return;
            try {
              const state=await request('/api/v2/ue/assets/scan-requests?ue_project_id='+encodeURIComponent(ue));
              if(token!==sequence || key!==context())return;
              if(state.request_id!==result.request_id)throw new Error('另一页面已发起新的扫描，请读取最新清单后重试。');
              if(state.status==='failed')throw new Error(state.error || 'UE 扫描失败。');
              if(state.status==='completed'){await load();return;}
              if(Date.now()-started>60000)throw new Error('尚未收到 UE 扫描结果。请保持绑定工程打开并启用目录同步，稍后点击“读取最新清单”。');
              notice.value='等待 UE 返回资产清单，请保持对应工程打开。';
              timer=setTimeout(poll,1500);
            }catch(e){if(token===sequence){stop();error.value=e.message;notice.value='保留上次同步清单。';}}
          };
          await poll();
        }catch(e){if(token===sequence){stop();error.value=e.message;}}
      }
      function choose(asset) {
        if(props.disabled || scanning.value || loading.value || !asset.runtime_supported)return;
        selected.value=asset.object_path;emit('select',selection(asset,catalog.value,props.dataset));
      }
      watch(context,()=>{catalog.value=null;folder.value='';query.value='';kind.value='';descendants.value=false;expanded.value=new Set();load();},{immediate:true});
      onUnmounted(()=>{++sequence;stop();});
      return {catalog,loading,scanning,error,notice,folder,query,kind,page,pages,items,filtered,selected,
        kinds,kindLabel,stamp,reason,load,scan,choose,descendants,expanded,treeRows,subfolders,breadcrumbs,covered,
        openFolder,toggleFolder,assetFolder};
    },
    template:`
    <section class="ue-picker" aria-label="工程资产">
      <p v-if="!dataset?.bound_ue_project_id">当前项目尚未绑定 UE 工程，请先到项目管理完成工程绑定。</p>
      <template v-else>
        <p><strong>{{ dataset.bound_ue_project_name || catalog?.ue_project_name || dataset.bound_ue_project_id }}</strong>
          <span> · 上次同步：{{ stamp(catalog?.synced_at) }}</span></p>
        <p v-if="catalog">清单范围：{{ catalog.roots?.join('、') || '尚未扫描' }}（含子目录）</p>
        <div class="ue-picker-controls">
          <button type="button" @click="scan" :disabled="!folder || !(folder === '/Game' || folder.startsWith('/Game/')) || !catalog || loading || scanning || disabled">{{ scanning ? '正在等待 UE…' : '从 UE 更新当前目录' }}</button>
          <button type="button" @click="load" :disabled="loading || disabled">读取最新清单</button>
        </div>
        <p>目录更新与 CAD 类型审核共用同一份清单；只替换所选目录及子目录，保留其他目录。</p>
        <p role="status" aria-live="polite">{{ loading ? '正在读取资产清单…' : notice }}</p>
        <p v-if="error" role="alert" class="ue-picker-error">{{ error }}</p>
        <div class="ue-picker-browser" v-if="catalog">
          <nav class="ue-picker-tree" aria-label="资产目录">
            <strong>目录</strong>
            <div v-for="node in treeRows" :key="node.path" class="ue-picker-tree-row" :class="{'is-current':folder===node.path}" :style="{'padding-left':(node.depth*16)+'px'}">
              <button v-if="node.children.length" type="button" class="ue-picker-toggle" @click="toggleFolder(node.path)" :aria-expanded="expanded.has(node.path)" :aria-label="(expanded.has(node.path)?'收起 ':'展开 ')+node.label">{{ expanded.has(node.path)?'−':'+' }}</button>
              <span v-else class="ue-picker-toggle-space"></span>
              <button type="button" class="ue-picker-folder" @click="openFolder(node.path)" :aria-current="folder===node.path?'location':undefined" :disabled="disabled || scanning">
                <span>{{ node.label }}</span><small>{{ node.count }}</small>
              </button>
            </div>
            <p>数字为已同步模型数（含子目录）。</p>
          </nav>
          <div class="ue-picker-content">
            <nav class="ue-picker-breadcrumbs" aria-label="当前目录">
              <template v-for="(crumb,index) in breadcrumbs" :key="crumb.path">
                <span v-if="index" aria-hidden="true">/</span>
                <button type="button" @click="openFolder(crumb.path)" :disabled="disabled || scanning">{{ crumb.label }}</button>
              </template>
            </nav>
            <p class="ue-picker-path">UE 目录：{{ folder }}</p>
            <p v-if="!covered" class="ue-picker-scope-note">当前目录未完整扫描，可进入已同步的子目录，或点击“从 UE 更新当前目录”。</p>
        <div class="ue-picker-controls">
          <label>模型类别<select v-model="kind"><option value="">全部类别</option>
            <option v-for="(label,key) in kinds" :key="key" :value="key">{{ label }}</option></select></label>
          <label class="ue-picker-search">搜索<input v-model="query" type="search" placeholder="在当前目录搜索名称或路径"></label>
        </div>
        <label class="ue-picker-recursive"><input type="checkbox" v-model="descendants"> 包含子目录中的模型</label>
        <div class="ue-picker-list" :aria-busy="loading || scanning">
          <table>
            <thead><tr><th scope="col">名称</th><th scope="col">模型类别</th><th scope="col">操作</th></tr></thead>
            <tbody>
              <tr v-for="child in subfolders" :key="child.path" class="ue-picker-directory">
                <td><button type="button" @click="openFolder(child.path)" :disabled="disabled || scanning">{{ child.label }}</button></td>
                <td>文件夹</td><td><button type="button" @click="openFolder(child.path)" :disabled="disabled || scanning">打开</button></td>
              </tr>
              <tr v-for="asset in items" :key="asset.object_path" :class="{'is-selected':selected===asset.object_path}">
                <td><button type="button" class="ue-picker-asset-name" @click="choose(asset)" :disabled="!asset.runtime_supported || loading || scanning || disabled">{{ asset.display_name || asset.asset_name }}</button>
                  <p v-if="descendants" class="ue-picker-path">{{ assetFolder(asset) }}</p>
                  <p v-if="!asset.runtime_supported">{{ reason(asset) }}</p></td>
                <td>{{ kindLabel(asset.asset_kind) }}</td>
                <td><button type="button" @click="choose(asset)" :disabled="!asset.runtime_supported || loading || scanning || disabled"
                  :aria-pressed="selected===asset.object_path">{{ selected===asset.object_path ? '已选择' : '选择' }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="!loading && !items.length">当前目录没有符合条件的模型。可打开子目录、勾选“包含子目录中的模型”，或调整筛选条件。</p>
        <p v-if="selected" class="ue-picker-selection">已选择：{{ selected }}</p>
        <div v-if="filtered.length" class="ue-picker-controls">
          <button type="button" @click="page--" :disabled="page<=1">上一页</button>
          <span>第 {{ page }} / {{ pages }} 页 · 共 {{ filtered.length }} 个模型</span>
          <button type="button" @click="page++" :disabled="page>=pages">下一页</button>
        </div>
          </div>
        </div>
      </template>
    </section>`
  };
  if(typeof module!=='undefined' && module.exports)module.exports={kindLabel,selection,buildFolders,filterAssets,assetFolder,insideFolder};
  else root.OntoTwinUEAssetPicker=component;
})(typeof window!=='undefined'?window:globalThis);
