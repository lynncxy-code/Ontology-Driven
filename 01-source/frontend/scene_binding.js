/* Explicit scene binding. Page context changes never rebind a UE level. */
(() => {
  const modal = document.createElement('dialog');
  modal.className = 'modal';
  modal.setAttribute('aria-labelledby', 'sceneBindingTitle');
  modal.innerHTML = `<h2 id="sceneBindingTitle">关卡绑定</h2>
    <p id="sceneBindingTarget"></p>
    <p>绑定后，该关卡固定使用此数据集。网页切换项目不会改变绑定。</p>
    <div class="field"><label for="sceneBindingChoice">选择已启动的工程与关卡</label><select id="sceneBindingChoice"></select></div>
    <p id="sceneBindingStatus" role="status"></p>
    <div class="modal-actions"><button class="btn" id="sceneBindingCancel">取消</button><button class="btn primary" id="sceneBindingSave">确认绑定</button></div>`;
  document.body.append(modal);
  const choice = modal.querySelector('select');
  const status = modal.querySelector('[role=status]');
  const save = modal.querySelector('#sceneBindingSave');
  let projectId = '', items = [], replaceId = '', busy = false;
  async function api(path, body) {
    const response = await fetch(path, { method: body ? 'POST' : 'GET', credentials: 'same-origin',
      headers: {'Content-Type':'application/json'}, ...(body ? {body:JSON.stringify(body)} : {}) });
    const data = await response.json();
    if (!response.ok) throw Object.assign(new Error(data.message || data.error), data);
    return data;
  }
  modal.querySelector('#sceneBindingCancel').onclick = () => { if (!busy) modal.close(); };
  modal.addEventListener('cancel', e => { if (busy) e.preventDefault(); });
  choice.onchange = () => { replaceId = ''; save.textContent = '确认绑定'; status.textContent = ''; };
  document.addEventListener('click', async event => {
    const trigger = event.target.closest('[data-bind-project]');
    if (!trigger) return;
    projectId = trigger.dataset.bindProject;
    modal.querySelector('#sceneBindingTarget').textContent = '目标数据集：' + trigger.dataset.bindName;
    choice.replaceChildren(); replaceId = ''; save.disabled = true; save.textContent = '确认绑定';
    status.textContent = '正在读取已发现的关卡…'; modal.showModal();
    try {
      const data = await api('/api/v2/ue/discovered');
      items = (data.items || []).filter(x => x.scene_id);
      items.forEach((x, i) => choice.add(new Option(`${x.ue_project_name} / ${x.scene_id}`, String(i))));
      status.textContent = items.length ? '请核对目标关卡后确认。' : '尚未发现关卡。请启动 UE 场景，确认后端地址正确后重新打开此窗口。';
      save.disabled = !items.length;
    } catch (e) { status.textContent = e.message; }
  });
  save.onclick = async () => {
    if (busy) return;
    const item = items[Number(choice.value)];
    if (!item) return;
    busy = true; save.disabled = true; choice.disabled = true;
    try {
      const ue = await api('/api/v4.8/ue/projects', {stable_key:item.ue_project_id, display_name:item.ue_project_name});
      const scene = await api(`/api/v4.8/ue/projects/${encodeURIComponent(ue.ue_project_id)}/scenes`, {stable_key:item.scene_id, level_path:item.scene_id});
      await api('/api/v4.8/bindings', {project_id:projectId, ue_project_id:ue.ue_project_id, scene_id:scene.scene_id, ...(replaceId ? {replace_binding_id:replaceId} : {})});
      status.textContent = '绑定已保存。UE 将重新检查并加载此数据集。';
      save.textContent = '已绑定';
    } catch (e) {
      if (e.error === 'scene_binding_conflict') {
        replaceId = e.binding_id;
        status.textContent = `该关卡已绑定数据集 ${e.project_id}。再次确认将解除原绑定并改用当前目标数据集。`;
        save.textContent = '确认换绑';
      } else { status.textContent = e.message; replaceId = ''; }
      save.disabled = false;
    } finally { busy = false; choice.disabled = false; }
  };
})();
