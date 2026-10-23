/* CAD review uses the workbench modal; no writes occur until the final action. */
window.CadComponentReview = (() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g,
    char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const xy = values => (values || []).map(v => Number(v).toFixed(2)).join(', ');
  const pose = values => `${xy((values || []).slice(0, 3))} cm；朝向 ${Number(values?.[3] || 0).toFixed(1)}°`;
  const objectLabel = object => `${object.type_name} · ${object.instance_id || object.id} · CAD (${xy(object.source_xy)})`;
  function mount(box) { box.style.width = 'min(800px, 94vw)'; }
  const scroll = html => `<div style="max-height:48vh;overflow:auto;overflow-wrap:anywhere">${html}</div>`;
  const row = html => `<div style="padding:12px 0;border-bottom:1px solid var(--line)">${html}</div>`;

  async function request(payload) {
    const response = await fetch('/api/v2/coord/save_components', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || data.error || `HTTP ${response.status}`);
    return data;
  }

  async function run(payload, UI) {
    let review = await request({...payload, dry_run:true});
    if (review.unresolved.length) {
      const existing = new Map(review.existing.map(item => [item.id, item]));
      const body = review.rows.filter(item => item.state === 'unresolved').map(item =>
        row(`<label>${esc(item.type_name)} · CAD (${esc(xy(item.source_xy))})` +
          `${item.equipment_id ? ` · 设备号 ${esc(item.equipment_id)}` : ''}` +
          `<select data-index="${item.index}" style="display:block;width:100%;margin-top:8px">` +
          `<option value="">请选择对应关系</option><option value="new">作为新增构件</option>` +
          item.candidates.map(id => `<option value="${esc(id)}">${esc(objectLabel(existing.get(id)))}</option>`).join('') +
          '</select></label>')).join('');
      const matches = await UI.modal({
        title:'确认构件对应关系',
        bodyHTML:'这些构件无法可靠匹配。请选择旧构件或明确作为新增；同一旧构件只能选择一次。' +
          scroll(body) + '<p data-error role="status"></p>',
        actions:[{label:'取消',value:null},{label:'预览变更',value:true,primary:true}],
        onMount(box) {
          mount(box);
          const selects = [...box.querySelectorAll('select[data-index]')];
          const validate = () => {
            const values = selects.map(el => el.value);
            const old = values.filter(value => value && value !== 'new');
            const duplicate = new Set(old).size !== old.length;
            box.querySelector('.btn-primary').disabled = duplicate || values.some(value => !value);
            box.querySelector('[data-error]').textContent = duplicate ? '同一个旧构件不能重复选择。' : '';
          };
          selects.forEach(el => el.addEventListener('change', validate)); validate();
        },
        beforeClose(value, box) {
          return value === true ? Object.fromEntries([...box.querySelectorAll('select[data-index]')]
            .map(el => [el.dataset.index, el.value])) : null;
        }
      });
      if (!matches) return null;
      payload = {...payload, matches};
      review = await request({...payload, dry_run:true});
      if (review.unresolved.length) throw new Error('仍有未确认的对应关系，请重新预览。');
    }
    const summary = review.summary;
    const changed = review.rows.filter(item => item.position_changed);
    const missing = new Set(review.missing);
    const changedHTML = changed.map(item => row(
      `<label><input type="checkbox" data-position="${esc(item.component_id)}"> ` +
      `将 ${esc(item.instance_id || item.component_id)} 更新到 CAD 位置</label>` +
      `<div>当前：${esc(pose(item.current_pose))}<br>CAD：${esc(pose(item.cad_pose))}</div>`)).join('');
    const addedHTML = review.rows.filter(item => item.state === 'new').map(item => row(
      `新增 ${esc(item.type_name)} · CAD (${esc(xy(item.source_xy))})`)).join('');
    const unboundHTML = review.rows.filter(item => item.cad_position_changed && !item.instance_id)
      .map(item => row(`更新未绑定构件：${esc(item.type_name)} · ${esc(item.component_id)}` +
        `<div>当前：${esc(pose(item.current_pose))}<br>CAD：${esc(pose(item.cad_pose))}</div>`)).join('');
    const missingHTML = review.existing.filter(item => missing.has(item.id))
      .map(item => row(`保留未出现构件：${esc(objectLabel(item))}`)).join('');
    const selected = await UI.modal({
      title:'预览 CAD 构件更新',
      bodyHTML:`<p>底图：${esc(review.frame_name)}</p>` +
        `<p>新增 ${summary.new} · 匹配 ${summary.matched} · 位置差异 ${summary.position_changes} · 保留未出现 ${summary.retained_missing}</p>` +
        '<p>匹配的构件保留编号和绑定；未绑定构件采用新版 CAD 坐标。已绑定构件默认保留现场位置，仅勾选的对象更新位置与朝向。</p>' +
        (review.legacy_unassigned ? `<p>另有 ${review.legacy_unassigned} 个同名历史构件缺少独立底图标识，本次保留，请在实例绑定台核对。</p>` : '') +
        (changed.length ? '<label><input type="checkbox" data-all> 全选位置更新</label>' : '') +
        scroll(changedHTML + unboundHTML + addedHTML + missingHTML),
      actions:[{label:'取消',value:null},{label:'确认保存',value:true,primary:true}],
      onMount(box) {
        mount(box);
        const all = box.querySelector('[data-all]');
        const checks = [...box.querySelectorAll('[data-position]')];
        all?.addEventListener('change', () => checks.forEach(el => { el.checked = all.checked; }));
        checks.forEach(el => el.addEventListener('change', () => {
          all.checked = checks.every(item => item.checked);
          all.indeterminate = !all.checked && checks.some(item => item.checked);
        }));
      },
      beforeClose(value, box) {
        return value === true ? [...box.querySelectorAll('[data-position]:checked')]
          .map(el => el.dataset.position) : null;
      }
    });
    if (selected === null) return null;
    payload = {...payload, apply_position_ids:selected};
    const finalReview = await request({...payload, dry_run:true});
    if (finalReview.basis_token !== review.basis_token) {
      throw new Error('预览期间图纸、构件或现场位置已变化，请重新预览后保存。');
    }
    return request({...payload, preview_token:finalReview.preview_token});
  }
  return {run};
})();
