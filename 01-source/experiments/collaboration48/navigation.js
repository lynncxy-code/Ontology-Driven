(() => {
    'use strict';
    const management = ['/organization','/account'].includes(location.pathname);
    const allowed = new Set(['/ontology_graph','/ontology','/binding','/coord','/interaction','/instance','/trash','/organization','/floor_pulse','/cad_generator']);
    const safeView = value => {try {const u=new URL(value,location.origin);return u.origin===location.origin&&allowed.has(u.pathname)?u.pathname+u.search:'/ontology_graph?nexus=true';}catch{return '/ontology_graph?nexus=true';}};
    async function session(){return (await fetch('/_collab48/api/state',{cache:'no-store'})).json();}
    if (management) return;
    const frame = document.getElementById('main-frame');
    if (!frame) {
        if (window===top) {
            const strip=document.createElement('div');strip.className='ot48-standalone';
            const back=document.createElement('a');back.href='/nexus?view='+encodeURIComponent(location.pathname+location.search);back.textContent='返回 Nexus 工作台';
            const manage=document.createElement('a');manage.href='/organization';manage.textContent='组织与账号管理';
            strip.append(back,manage);document.body.prepend(strip);
        }
        return;
    }
    let lastWork=safeView(sessionStorage.getItem('ot48-last-work')||'/ontology_graph?nexus=true');
    if(lastWork.startsWith('/organization'))lastWork='/ontology_graph?nexus=true';
    function go(title,url,element) {
        const target=safeView(url);
        if(!target.startsWith('/organization')){lastWork=target;sessionStorage.setItem('ot48-last-work',target);}
        frame.contentWindow.location.replace(target);
        window.syncActiveMenu?.(target);
        history.pushState({view:target},'', '/nexus?view='+encodeURIComponent(target));
    }
    function confirmLeave(proceed) {
        let editing=false;
        try{editing=frame.contentWindow.location.pathname==='/organization'&&!!frame.contentDocument.querySelector('dialog[open]');}catch{}
        if(!editing){proceed();return;}
        const dialog=document.createElement('dialog');dialog.className='ot48-leave';
        dialog.innerHTML='<h3>管理表单尚未提交</h3><p>离开会放弃当前表单输入，已保存的信息不受影响。</p><div><button type="button" data-stay>继续填写</button><button type="button" data-leave>放弃并离开</button></div>';
        document.body.append(dialog);dialog.showModal();
        dialog.querySelector('[data-stay]').onclick=()=>dialog.close();
        dialog.querySelector('[data-leave]').onclick=()=>{dialog.close();proceed();};
        dialog.onclose=()=>dialog.remove();
    }
    window.navigate=(title,url,element)=>{
        confirmLeave(()=>go(title,url,element));
    };
    const target=safeView(new URLSearchParams(location.search).get('view')||'/ontology_graph?nexus=true');
    if(!target.startsWith('/organization')){lastWork=target;sessionStorage.setItem('ot48-last-work',target);}
    frame.contentWindow.location.replace(target);
    window.addEventListener('popstate',()=>{frame.contentWindow.location.replace(safeView(new URLSearchParams(location.search).get('view')||'/ontology_graph?nexus=true'));});
    const bar=document.querySelector('.topbar');
    document.getElementById('release-badge')?.remove();
    const label=document.createElement('span');label.className='ot48-test-label';label.textContent='4.8 联通测试 · 独立数据';bar.prepend(label);
    const organization=document.createElement('button');organization.className='ot48-org';organization.textContent='组织与账号管理';
    organization.onclick=()=>window.navigate('组织与账号管理','/organization',organization);
    bar.querySelector('.breadcrumb')?.replaceWith(organization);
    const oldProfile=document.querySelector('.user-profile');
    const account=document.createElement('div');account.className='ot48-account';oldProfile?.replaceWith(account);
    const exit=document.createElement('button');exit.className='ot48-org';exit.textContent='退出登录';
    exit.onclick=()=>confirmLeave(async()=>{await fetch('/_collab48/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.replace('/account?next='+encodeURIComponent('/nexus?view='+encodeURIComponent(lastWork)));});
    account.after(exit);
    const update=async()=>{const s=await session();if(!s.me||s.me.first_login){location.replace('/account?next='+encodeURIComponent(location.pathname+location.search));return;}organization.textContent=s.org.group+' / '+s.org.factory+' · 组织与账号管理';account.textContent=s.me.name+' · '+({admin:'管理员',editor:'编辑者',viewer:'查看者'}[s.me.role]);};
    window.addEventListener('message',e=>{if(e.origin!==location.origin||e.source!==frame.contentWindow)return;if(e.data?.type==='ot48-return')window.navigate('返回工作页',lastWork,organization);if(e.data?.type==='ot48-account-updated')update();});
    update().catch(()=>{label.textContent='测试服务暂不可用';});
})();
