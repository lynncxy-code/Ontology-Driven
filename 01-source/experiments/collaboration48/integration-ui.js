// Integration-only adapter: keep the existing prototype usable independently.
const baseRender48 = render;
function destination48() {
    const next = new URLSearchParams(location.search).get('next') || '/nexus';
    const url = new URL(next, location.origin);
    return url.origin === location.origin && ['/nexus','/ontology_graph','/ontology','/binding','/coord','/interaction','/instance','/trash','/organization'].includes(url.pathname) ? url.pathname + url.search : '/nexus';
}
render = function() {
    if (location.pathname === '/account' && window !== top) {
        top.location.replace(location.href);
        return;
    }
    if (state.me && !state.me.first_login && location.pathname === '/account') {
        location.replace(destination48());
        return;
    }
    if (!state.me && location.pathname !== '/account') {
        top.location.href='/account?next='+encodeURIComponent('/nexus');
        return;
    }
    baseRender48();
    document.querySelector('.auth details')?.remove();
    if (state.me && !state.me.first_login) {
        document.body.classList.add('integrated-management');
        // Existing Nexus owns navigation and account chrome when embedded.
        document.body.classList.toggle('embedded-management', window !== window.top);
        const content=document.querySelector('.content');
        const back=document.createElement('button');
        back.type='button'; back.className='return-workspace'; back.textContent='返回工作页面';
        back.onclick=()=>window===top?location.assign('/nexus'):parent.postMessage({type:'ot48-return'},location.origin);
        content?.prepend(back);
        document.querySelectorAll('[data-page="projects"]').forEach(b=>b.onclick=()=>top.location.assign('/nexus?view='+encodeURIComponent('/ontology_graph?nexus=true')));
        document.querySelector('[data-page="scenes"]')?.remove();
        const caption=document.querySelector('aside .footnote');
        if(caption)caption.textContent='4.8 独立联通测试环境';
        document.querySelectorAll('[data-page="organization"],[data-page="members"]').forEach(b=>{
            b.addEventListener('click',()=>{
                history.replaceState({},'', '/organization?tab='+b.dataset.page);
            });
        });
        parent.postMessage({type:'ot48-account-updated'},location.origin);
    }
};
