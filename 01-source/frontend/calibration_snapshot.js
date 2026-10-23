/* Portable UE calibration snapshot v1. Parsing and pairing do not write project data. */
(function(root) {
  'use strict';
  const MAX_BYTES = 48 * 1024 * 1024;
  const esc = value => String(value ?? '').replace(/[&<>"']/g,
    ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const coords = point => point.map(value => Number(value).toFixed(2)).join(', ');
  const vector = (value, size) => Array.isArray(value) && value.length === size &&
    value.every(number => typeof number === 'number' && Number.isFinite(number) && Math.abs(number) < 1e12);
  function hasArea(points) {
    let span = 0, area = 0;
    for (let i = 1; i < points.length; i++) {
      const a = points[i].map((v, k) => v - points[0][k]);
      span = Math.max(span, a[0] * a[0] + a[1] * a[1]);
      for (let j = i + 1; j < points.length; j++) {
        const b = points[j].map((v, k) => v - points[0][k]);
        span = Math.max(span, (a[0]-b[0])**2+(a[1]-b[1])**2);
        area = Math.max(area, Math.abs(a[0] * b[1] - a[1] * b[0]));
      }
    }
    return span > 1 && area / span >= 0.05;
  }
  function validate(data) {
    if (!data || data.schema !== 'ontotwin.calibration-snapshot' || data.version !== 1 || data.units !== 'cm')
      throw new Error('请选择 UE 导出的标定快照（版本 1，坐标单位 cm），普通截图不能直接导入。');
    if (typeof data.snapshot_id !== 'string' || !/^[a-zA-Z0-9-]{1,64}$/.test(data.snapshot_id))
      throw new Error('快照标识无效。');
    const source = data.source;
    if (!source || typeof source.project_name !== 'string' || !source.project_name.trim() ||
        typeof source.level !== 'string' || !source.level.trim() ||
        typeof source.ue_project_id !== 'string' ||
        [source.project_name, source.level, source.ue_project_id].some(value => value.length > 512))
      throw new Error('快照缺少有效的工程或关卡信息。');
    const image = data.image;
    if (!image || image.mime_type !== 'image/png' || !Number.isInteger(image.width) ||
        !Number.isInteger(image.height) || image.width < 100 || image.height < 100 ||
        image.width * image.height > 16777216 || typeof image.data_base64 !== 'string' ||
        image.data_base64.length > 44 * 1024 * 1024 ||
        !/^[A-Za-z0-9+/]+={0,2}$/.test(image.data_base64) || image.data_base64.length % 4)
      throw new Error('快照截图格式或尺寸无效。');
    const header = atob(image.data_base64.slice(0, 44));
    const png = [137,80,78,71,13,10,26,10];
    const uint32 = offset => [...header.slice(offset, offset + 4)].reduce((n, ch) => n * 256 + ch.charCodeAt(0), 0);
    if (header.length < 24 || png.some((byte, i) => header.charCodeAt(i) !== byte) ||
        header.slice(12,16) !== 'IHDR' || uint32(16) !== image.width || uint32(20) !== image.height)
      throw new Error('截图内容与声明的尺寸不一致。');
    if (!Array.isArray(data.points) || data.points.length < 3 || data.points.length > 32)
      throw new Error('快照需要包含 3 至 32 个参考点。');
    const ids = new Set();
    for (const point of data.points) {
      if (!point || typeof point.id !== 'string' || !/^P[1-9][0-9]{0,3}$/.test(point.id) ||
          ids.has(point.id) || !vector(point.ue_world_cm, 3) || !vector(point.image_xy, 2) ||
          point.image_xy[0] < 0 || point.image_xy[0] >= image.width ||
          point.image_xy[1] < 0 || point.image_xy[1] >= image.height)
        throw new Error('参考点存在重复点号、无效坐标或超出截图范围。');
      ids.add(point.id);
    }
    if (!hasArea(data.points.map(point => point.ue_world_cm)))
      throw new Error('参考点接近共线，请回 UE 重新选取分布较开的点。');
    const heights = data.points.map(point => point.ue_world_cm[2]);
    if (Math.max(...heights) - Math.min(...heights) > 5)
      throw new Error('参考点高度差超过 5 cm，请使用同一标定平面的点。');
    return data;
  }
  function checkSource(data, context) {
    if (context.ueProjectId && data.source.ue_project_id && context.ueProjectId !== data.source.ue_project_id)
      throw new Error('快照来自其他 UE 工程，请切换到对应项目或重新导出。');
    if (context.level?.trim() && context.level.trim() !== data.source.level.trim())
      throw new Error('快照关卡与当前 CAD 底图填写的 UE 关卡不同，请先核对关卡。');
  }
  function anchors(data, pairs) {
    const result = data.points.map(point => {
      const xy = pairs[point.id];
      if (!vector(xy, 2)) throw new Error(`请先在 CAD 上指定 ${point.id} 的对应位置。`);
      return {id:point.id, cadXY:xy.slice(), readings:{ue:point.ue_world_cm.slice()}};
    });
    if (!hasArea(result.map(point => point.cadXY)))
      throw new Error('CAD 对应点接近共线，请重新配对。');
    return result;
  }
  function create(options) {
    const {UI, container, getContext, applyAnchors, toast} = options;
    let stage = null, busy = false;
    let objectUrl=null;
    function reset(){
      stage=null;
      if(objectUrl)URL.revokeObjectURL(objectUrl);
      objectUrl=null;render();
    }
    const imageUrl = () => objectUrl;
    function requireContext(context) {
      if (!context.ready) throw new Error('请先加载并保存当前 CAD 底图，再导入 UE 快照。');
      if (context.target !== 'ue') throw new Error('请将映射目标切换到 UE，再使用标定快照。');
    }
    function current() {
      const context = getContext();
      requireContext(context);
      if (!stage || context.key !== stage.context.key) throw new Error('项目、底图或楼层已切换，请重新导入快照。');
      checkSource(stage.data, context);
      return context;
    }
    function render() {
      container.replaceChildren();
      if (!stage) return;
      const data = stage.data;
      container.innerHTML = `<p class="hint">${esc(data.source.project_name)} · ${esc(data.source.level)}</p>` +
        '<button type="button" class="snapshot-image" data-image aria-label="放大 UE 标定快照"><img alt="UE 标定参考点快照"></button>' +
        `<p class="hint" role="status">${stage.active ? `请在左侧 CAD 上点击 ${esc(stage.active)} 的对应位置。` : '点位已配对。可选中任一点重新配对，或应用后计算变换。'}</p>` +
        data.points.map(point => `<button type="button" class="btn btn-sm snapshot-point${stage.active === point.id ? ' is-active' : ''}" data-point="${point.id}" aria-pressed="${stage.active === point.id}">` +
          `<b>${point.id}</b><span>UE (${coords(point.ue_world_cm)}) cm<br>` +
          `${stage.pairs[point.id] ? `CAD (${coords(stage.pairs[point.id])})` : '等待点击 CAD 对应位置'}</span></button>`).join('') +
        '<p class="hint">仅配对平面位置，楼层高度沿用当前楼层配置。应用前不会修改原有锚点。</p>' +
        (data.points.length===3 ? '<p class="hint">只有 3 点时仿射拟合误差必为零，不能据此证明配对正确。建议回 UE 至少采集 4 点，或使用独立核验点检查。</p>' : '') +
        '<div class="snapshot-actions"><button type="button" class="btn btn-sm" data-exit>退出配对</button>' +
        '<button type="button" class="btn btn-sm" data-apply>应用标定点</button></div>';
      container.querySelector('img').src = imageUrl(data);
      container.querySelector('[data-image]').onclick = () => UI.modal({
        title:'UE 标定快照', bodyHTML:'<img data-full alt="UE 标定参考点快照" style="width:100%;height:auto">',
        actions:[{label:'返回配对',value:true,primary:true}],
        onMount(box) {box.style.width='min(1200px,94vw)';box.querySelector('img').src=imageUrl(data);}
      });
      container.querySelectorAll('[data-point]').forEach(button => {
        button.onclick = () => {stage.active=button.dataset.point;stage.applied=false;render();};
      });
      container.querySelector('[data-exit]').onclick = reset;
      const apply = container.querySelector('[data-apply]');
      apply.disabled = data.points.some(point => !stage.pairs[point.id]);
      apply.onclick = async () => {
        if (busy) return;
        busy=true;apply.disabled=true;
        try {
          current();
          const pending=stage, result=anchors(data, stage.pairs);
          const ok=await UI.confirm({title:'应用 UE 标定点',
            bodyHTML:`将用这 ${result.length} 个配对点替换当前锚点，并清除旧计算结果。之后请重新计算误差、保存并发布。`,
            confirmText:'应用标定点'});
          if(!ok)return;
          if(stage!==pending)throw new Error('快照已变化，请重新检查配对。');
          current();
          applyAnchors(result);
          stage.active=null;stage.applied=true;
          toast('标定点已填入，请计算变换并检查误差。','ok');
        }catch(error){toast(error.message,'err');}
        finally{busy=false;render();}
      };
    }
    return {
      reset,
      resetIfContextChanged(){if(stage && getContext().key!==stage.context.key)reset();},
      async importFile(file) {
        if (!file || busy) return;
        busy=true;
        try {
          const context=getContext();requireContext(context);
          if (file.size > MAX_BYTES) throw new Error('快照超过 48 MB，请在 UE 中缩小视口后重新导出。');
          let raw;
          try {raw=JSON.parse(await file.text());} catch {throw new Error('文件不是有效的标定快照，请重新导出。');}
          const data=validate(raw);checkSource(data,context);
          reset();
          const bytes=Uint8Array.from(atob(data.image.data_base64),ch=>ch.charCodeAt(0));
          objectUrl=URL.createObjectURL(new Blob([bytes],{type:'image/png'}));
          await new Promise((resolve,reject)=>{
            const img=new Image();
            img.onload=()=>img.naturalWidth===data.image.width&&img.naturalHeight===data.image.height?resolve():reject(new Error('截图尺寸不匹配。'));
            img.onerror=()=>reject(new Error('快照截图已损坏，请重新导出。'));
            img.src=imageUrl(data);
          });
          const sourceVerified=!!(context.ueProjectId && data.source.ue_project_id);
          const ok=await UI.modal({title:'导入 UE 标定快照',
            bodyHTML:`工程：${esc(data.source.project_name)}<br>关卡：${esc(data.source.level)}<br>参考点：${data.points.length} 个` +
              (!sourceVerified?'<p>快照或当前项目缺少 UE 工程标识，请根据工程名、关卡和截图确认来源。</p>':'') +
              '<img data-snapshot-preview alt="待导入的 UE 标定快照" style="display:block;width:100%;height:auto;margin:12px 0">' +
              '<p>下一步按点号点击 CAD 对应位置。现有标定会保留到你明确应用新点位。</p>',
            actions:[{label:'取消',value:false},{label:'开始配对',value:true,primary:true}],
            onMount(box){box.querySelector('[data-snapshot-preview]').src=imageUrl(data);}});
          if(!ok){reset();return;}
          const now=getContext();requireContext(now);
          if(now.key!==context.key)throw new Error('项目、底图或楼层已切换，请重新导入。');
          checkSource(data,now);
          stage={data,context:now,pairs:{},active:data.points[0].id};render();
        }catch(error){reset();toast(error.message,'err');}
        finally{busy=false;}
      },
      pick(x,y) {
        if(!stage)return false;
        if(getContext().key!==stage.context.key){reset();return false;}
        if(!stage.active) {
          if(stage.applied)return false;
          toast('已配对全部点，请应用标定点，或先选择一个点重新配对。','warn');
          return true;
        }
        try {
          current();
          if(busy)return true;
          stage.pairs[stage.active]=[x,y];
          stage.active=stage.data.points.find(point=>!stage.pairs[point.id])?.id||null;
          render();
        }catch(error){toast(error.message,'err');}
        return true;
      }
    };
  }
  const api={validate,checkSource,anchors,create,hasArea};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.CalibrationSnapshot=api;
})(typeof window!=='undefined'?window:globalThis);
