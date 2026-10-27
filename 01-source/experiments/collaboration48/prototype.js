(() => {
  'use strict';
  const root = document.querySelector('#prototype');
  const dialog = document.querySelector('#dialog');
  const key = 'ontotwin48-ui-prototype-v2';
  const initial = () => ({orgs:[
    {id:'mine',name:'我的本体工厂',factory:'本地试验工厂',logo:'',projects:[{id:'standard',name:'标准实践'}],members:[{name:'体验管理员',account:'admin',role:'管理员',projects:['standard']}]},
    {id:'a',name:'工厂 A · 示例组织',factory:'工厂 A',logo:'',projects:[{id:'assembly',name:'装配车间 · 示例'}],members:[{name:'体验管理员',account:'admin',role:'管理员',projects:['assembly']}]},
    {id:'b',name:'工厂 B · 示例组织',factory:'工厂 B',logo:'',projects:[],members:[{name:'体验管理员',account:'admin',role:'管理员',projects:[]}]}
  ],displayName:'体验管理员'});
  let data; try { data = JSON.parse(localStorage.getItem(key)) || initial(); } catch { data = initial(); }
  let logged = sessionStorage.getItem(key) === 'in', orgId=sessionStorage.getItem(key+'-org'), page='datasets', projectId=null, tab='basic', menu='', dirty=false;
  if(!logged || !data.orgs.some(o=>o.id===orgId)) orgId=null;
  const esc = x => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const org = () => data.orgs.find(o=>o.id===orgId);
  const project = () => org().projects.find(p=>p.id===projectId);
  const currentMember = () => org()?.members.find(m=>m.account==='admin');
  const isAdmin = () => currentMember()?.role==='管理员';
  const save = () => localStorage.setItem(key,JSON.stringify(data));
  const brand = '<div class="brand"><img src="/_collab48/brand.svg" alt="OntoTwin"><div><strong>OntoTwin Nexus</strong><small>本体驱动工业数字孪生平台</small></div></div>';
  const logo = (o,large=false) => o.logo ? `<img class="org-logo ${large?'large':''}" src="${esc(o.logo)}" alt="组织 Logo">` : `<span class="org-logo ${large?'large':''}">${esc(o.name.slice(0,1))}</span>`;
  const btn = (action,label,cls='') => `<button type="button" data-action="${action}" class="${cls}">${label}</button>`;
  function feedback(message){const box=document.querySelector('#feedback');box.textContent=message;box.hidden=false;setTimeout(()=>box.hidden=true,3500);}
  function modal(title,body){document.querySelector('#dialog-body').innerHTML=`<div class="dialog-head"><h2>${title}</h2>${btn('close','关闭','ghost')}</div>${body}`;dialog.showModal();}
  function navigate(fn){if(!dirty){fn();return;}modal('离开当前编辑？',`<p>尚未保存的原型表单将被放弃。已保存内容不受影响。</p><footer>${btn('close','继续编辑')}${btn('discard','放弃并继续','primary')}</footer>`);document.querySelector('[data-action=discard]').onclick=()=>{dirty=false;pendingLogo=null;dialog.close();fn();};}
  function updateMenu(){root.querySelectorAll('.menu').forEach(el=>el.remove());root.querySelector('.layout')?.insertAdjacentHTML('beforeend',menus());root.querySelectorAll('[aria-expanded]').forEach(el=>el.setAttribute('aria-expanded',String(menu===(el.dataset.action==='switch'?'org':el.dataset.action))));}
  function go(next){navigate(()=>{page=next;menu='';render();});}
  function menus(){
    if(menu==='org')return `<div class="menu org-menu">${btn('account','返回用户菜单','ghost')}<div class="caption">切换组织</div>${data.orgs.map(o=>`<button data-org="${o.id}" aria-current="${o.id===orgId}">${logo(o)}<span>${esc(o.name)}<br><small>${esc(o.factory)}</small></span>${o.id===orgId?'<span class="current-org">当前</span>':''}</button>`).join('')}</div>`;
    if(menu==='account')return `<div class="menu account-menu"><div class="identity"><strong>${esc(data.displayName)}</strong><small>${esc(currentMember()?.role||'成员')}</small><small>${esc(org().name)} / ${esc(org().factory)}</small></div>${btn('personal','个人设置')}${isAdmin()?btn('permissions','权限管理'):''}${btn('settings','组织设置')}${btn('switch','切换组织')}${btn('version','版本信息')}<hr>${btn('logout','退出登录')}</div>`;
    if(menu==='version')return `<div class="menu version-menu">${btn('account','返回用户菜单','ghost')}<div class="caption">版本信息</div><dl><dt>当前页面</dt><dd>4.8 交互原型 v0.2</dd><dt>数据范围</dt><dd>本浏览器模拟数据</dd><dt>业务前端参考</dt><dd>WEB-20261023-P3</dd></dl></div>`;
    return '';
  }
  function datasets(){return `<div class="page-head"><div><div class="eyebrow">${esc(org().name)} / ${esc(org().factory)}</div><h1>我的数据集</h1></div>${btn('create','新建空数据集','primary')}</div>${org().projects.length?org().projects.map(p=>`<section class="dataset ${projectId===p.id?'selected':''}"><div><h2>${esc(p.name)}</h2><div class="meta"><span>${esc(org().factory)}</span><span>未绑定 UE · 原型样例</span></div></div><button data-project="${p.id}">进入项目</button></section>`).join(''):'<div class="empty"><h2>这个组织还没有数据集</h2></div>'}`;}
  function settings(){return `<div class="page-head"><div><h1>组织设置</h1></div>${btn('datasets','返回工作台')}</div><div class="tabs"><button data-tab="basic" class="${tab==='basic'?'active':''}">基本信息</button><button data-tab="members" class="${tab==='members'?'active':''}">成员与权限</button></div>${tab==='basic'?`<form id="organization" class="settings"><div class="form-row"><div><h3>组织标识</h3></div><div class="logo-row">${logo(org(),true)}<label>上传 Logo<input id="logo-file" type="file" accept="image/png,image/jpeg,image/webp"></label></div></div><div class="form-row"><h3>组织信息</h3><div><label>组织名称<input name="name" required maxlength="50" value="${esc(org().name)}"></label><label>当前工厂<input name="factory" required maxlength="50" value="${esc(org().factory)}"></label></div></div><footer><button class="primary">保存修改</button></footer></form>`:`<div class="toolbar"><span>${org().members.length} 位成员</span>${btn('member','新增成员','primary')}</div><div class="table-box"><table><thead><tr><th>成员 / 账号</th><th>角色</th><th>项目范围</th><th>操作</th></tr></thead><tbody>${org().members.map((m,i)=>`<tr><td>${esc(m.name)}<small>${esc(m.account)}</small></td><td>${esc(m.role)}</td><td>${m.role==='管理员'?'本组织全部项目':esc(m.projects.map(id=>org().projects.find(p=>p.id===id)?.name).filter(Boolean).join('、')||'尚未授权')}</td><td><button data-member="${i}">编辑</button></td></tr>`).join('')}</tbody></table></div>`}`;}
  function permissions(){return `<div class="page-head"><div><h1>权限管理</h1><p>管理成员角色，以及每位成员可以编辑的项目。</p></div>${btn('datasets','返回工作台')}</div><div class="toolbar"><span>${org().members.length} 位成员</span>${btn('member','新增成员','primary')}</div><div class="table-box"><table><thead><tr><th>成员 / 账号</th><th>角色</th><th>项目范围</th><th>操作</th></tr></thead><tbody>${org().members.map((m,i)=>`<tr><td>${esc(m.name)}<small>${esc(m.account)}</small></td><td>${esc(m.role)}</td><td>${m.role==='管理员'?'本组织全部项目':esc(m.projects.map(id=>org().projects.find(p=>p.id===id)?.name).filter(Boolean).join('、')||'尚未授权')}</td><td><button data-member="${i}">编辑</button></td></tr>`).join('')}</tbody></table></div>`;}
  function personal(){return `<div class="page-head"><div><h1>个人设置</h1></div>${btn('datasets','返回工作台')}</div><form id="personal" class="settings"><label>显示名称<input name="name" required maxlength="30" value="${esc(data.displayName)}"></label><label>体验账号<input disabled value="admin"></label><footer><button class="primary">保存修改</button></footer></form>`;}
  function detail(){return `<div class="page-head"><div><div class="eyebrow">${esc(org().name)} / ${esc(org().factory)}</div><h1>${esc(project()?.name||'未选择数据集')}</h1></div>${btn('datasets','返回我的数据集')}</div><section class="settings"><h2>项目概览</h2><div class="definition"><div><span>归属组织</span>${esc(org().name)}</div><div><span>当前工厂</span>${esc(org().factory)}</div><div><span>UE 绑定</span>未绑定（原型）</div><div><span>编辑身份</span>体验管理员</div></div></section>`;}
  function render(){
    if(!logged){root.innerHTML=`<div class="login-wrap"><form id="login" class="login">${brand}<h1>登录工作台</h1><label>体验账号<input value="admin" readonly></label><button class="primary">体验登录</button></form></div>`;return;}
    if(!orgId){root.innerHTML=`<div class="login-wrap"><section class="login org-selection" aria-labelledby="org-heading">${brand}<div class="page-head"><button type="button" class="ghost step-arrow" data-action="logout" aria-label="返回登录"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg></button><h1 id="org-heading">选择组织</h1></div><div class="organization-options">${data.orgs.map(o=>`<button class="organization-option" data-org="${esc(o.id)}" aria-label="进入${esc(o.name)}">${logo(o)}<strong>${esc(o.name)}</strong><span class="step-arrow inline" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></span></button>`).join('')||'<div class="empty">暂无可进入的组织</div>'}</div></section></div>`;return;}
    root.innerHTML=`<div class="layout"><aside>${brand}<div class="nav-label">数据定义</div>${btn('datasets','<span class="nav-mark">◇</span>语义图谱总览',`nav-item ${['datasets','detail'].includes(page)?'active':''}`)}</aside><div class="work"><header class="topbar"><div class="context">${btn('datasets',esc(project()?.name||'选择数据集'),'ghost')}<small>/ ${page==='settings'?'组织设置':page==='permissions'?'权限管理':page==='personal'?'个人设置':'语义图谱总览'}</small></div><div class="top-actions"><button class="avatar" data-action="account" aria-label="打开用户菜单" aria-expanded="${menu==='account'}">${esc(data.displayName.slice(0,1))}</button></div></header><main>${page==='settings'?settings():page==='permissions'?permissions():page==='personal'?personal():page==='detail'?detail():datasets()}</main></div>${menus()}</div>`;
  }
  let pendingLogo;
  document.addEventListener('click',e=>{
    const o=e.target.closest('[data-org]');if(o){navigate(()=>{orgId=o.dataset.org;sessionStorage.setItem(key+'-org',orgId);projectId=null;page='datasets';menu='';render();});return;}
    const p=e.target.closest('[data-project]');if(p){projectId=p.dataset.project;go('detail');return;}
    const t=e.target.closest('[data-tab]');if(t){navigate(()=>{tab=t.dataset.tab;render();});return;}
    const m=e.target.closest('[data-member]');if(m){editMember(Number(m.dataset.member));return;}
    const a=e.target.closest('[data-action]')?.dataset.action;
    if(a==='close'){dialog.close();return;}
    if(a==='discard')return;
    if(['datasets','personal','settings','permissions'].includes(a)){go(a);return;}
    if(['switch','version','account'].includes(a)){const next=a==='switch'?'org':a;menu=menu===next?'':next;updateMenu();return;}
    if(a==='logout'){navigate(()=>{logged=false;orgId=null;projectId=null;menu='';sessionStorage.removeItem(key);sessionStorage.removeItem(key+'-org');render();});return;}
    if(a==='create'){modal('新建空数据集','<form id="create"><label>数据集名称<input name="name" required maxlength="60" autofocus></label><p>归属于当前组织：'+esc(org().name)+'</p><footer>'+btn('close','取消')+'<button class="primary">创建并进入</button></footer></form>');return;}
    if(a==='member'){editMember(-1);return;}
    if(menu&&!e.target.closest('.menu')){menu='';updateMenu();}
  });
  function editMember(index){const m=org().members[index]||{name:'',account:'',role:'编辑者',projects:[]};modal(index<0?'新增成员':'编辑成员',`<form id="member" data-index="${index}"><label>姓名<input name="name" value="${esc(m.name)}" required maxlength="30"></label><label>账号<input name="account" value="${esc(m.account)}" required pattern="[A-Za-z0-9_-]+" ${index>=0?'readonly':''}></label><label>角色<select name="role"><option ${m.role==='编辑者'?'selected':''}>编辑者</option><option ${m.role==='管理员'?'selected':''}>管理员</option><option ${m.role==='查看者'?'selected':''}>查看者</option></select></label><h3>授权项目</h3>${org().projects.map(p=>`<label class="check"><input type="checkbox" name="projects" value="${p.id}" ${m.projects.includes(p.id)?'checked':''}>${esc(p.name)}</label>`).join('')||'<p>当前没有项目，创建后再授权。</p>'}<p id="member-error" class="error"></p><footer>${btn('close','取消')}<button class="primary">保存成员</button></footer></form>`);}
  document.addEventListener('input',e=>{if(e.target.closest('#organization,#personal'))dirty=true;});
  document.addEventListener('change',e=>{if(e.target.id!=='logo-file')return;const f=e.target.files[0];if(!f)return;if(!['image/png','image/jpeg','image/webp'].includes(f.type)||f.size>1024*1024){feedback('请选择 1 MB 以内的 PNG、JPG 或 WebP。');e.target.value='';return;}const reader=new FileReader();reader.onload=()=>{pendingLogo=reader.result;dirty=true;};reader.readAsDataURL(f);});
  document.addEventListener('submit',e=>{e.preventDefault();const f=e.target,v=new FormData(f);
    if(f.id==='login'){logged=true;sessionStorage.setItem(key,'in');sessionStorage.removeItem(key+'-org');orgId=null;page='datasets';projectId=null;menu='';render();return;}
    if(f.id==='organization'){org().name=v.get('name').trim();org().factory=v.get('factory').trim();if(pendingLogo)org().logo=pendingLogo;pendingLogo=null;dirty=false;}
    if(f.id==='personal'){data.displayName=v.get('name').trim();dirty=false;}
    if(f.id==='create'){const p={id:'p'+Date.now(),name:v.get('name').trim()};if(!p.name)return;org().projects.push(p);projectId=p.id;page='detail';dialog.close();}
    if(f.id==='member'){const index=Number(f.dataset.index),account=v.get('account').trim();if(org().members.some((m,i)=>i!==index&&m.account===account)){document.querySelector('#member-error').textContent='该账号已存在，请使用其他账号。';return;}const m={name:v.get('name').trim(),account,role:v.get('role'),projects:v.getAll('projects')};if(index<0)org().members.push(m);else org().members[index]=m;dialog.close();}
    try{save();render();feedback('已保存到本浏览器的原型数据。');}catch{feedback('浏览器存储空间不足，请使用更小的 Logo。');}
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu){menu='';updateMenu();}});
  window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
  render();
})();
