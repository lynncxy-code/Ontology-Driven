/* Local synthetic monitor demo: only fixed channels 17–30, never camera capture. */
(() => {
  'use strict';
  const ids = Array.from({ length: 14 }, (_, i) => String(i + 17));
  const gateway = 'http://127.0.0.1:8889';
  const screen = document.getElementById('screen');
  const viewer = document.querySelector('.viewer');
  const heading = viewer.querySelector('.panel-heading');
  const viewerFooter = viewer.querySelector('.viewer-footer');
  function fitVideoFrame() {
    if (viewer.hidden) return;
    const style = getComputedStyle(viewer);
    const sideSpace = parseFloat(style.left) + parseFloat(style.right);
    const availableWidth = Math.max(0, innerWidth - sideSpace);
    const availableHeight = innerWidth <= 1100
      ? Math.max(0, innerHeight - 280 - (innerWidth <= 600 ? 8 : 24))
      : Math.min(innerHeight * .8, innerHeight - 32);
    // Measure wrapped controls at the available width before fitting the frame.
    viewer.style.width = `${availableWidth}px`;
    let chromeHeight, width;
    // Refine after shrinking the shell, since footer text can wrap on small screens.
    for (let pass = 0; pass < 3; pass++) {
      chromeHeight = heading.offsetHeight + viewerFooter.offsetHeight + 2;
      width = Math.max(0, Math.min(availableWidth - 18,
        (availableHeight - chromeHeight) * 16 / 9));
      viewer.style.width = `${width + 18}px`;
    }
    screen.style.width = `${width}px`;
    screen.style.height = `${width * 9 / 16}px`;
    viewer.style.height = `${width * 9 / 16 + chromeHeight}px`;


  }
  const frameObserver = new ResizeObserver(fitVideoFrame);
  [viewer, heading, viewerFooter].forEach(element => frameObserver.observe(element));
  const empty = screen.firstElementChild.cloneNode(true);
  const status = document.getElementById('player-status');
  const retry = document.getElementById('retry');
  const overview = document.getElementById('overview');
  const channels = document.getElementById('channels');
  let current = null;
  let generation = 0;
  let loadTimer;
  ids.forEach(id => {
    const link = document.createElement('a');
    link.className = 'channel';
    link.href = `/monitor-test.html?camera_id=${id}`;
    link.dataset.cameraId = id;
    const name = document.createElement('strong');
    name.textContent = `摄像头 ${id}`;
    const hint = document.createElement('span');
    hint.textContent = '点击播放';
    link.append(name, hint);
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (current !== id) select(id, true);
    });
    channels.append(link);
  });
  function select(id, pushHistory = false) {
    viewer.hidden = false;
    const valid = ids.includes(id);
    const token = ++generation;
    clearTimeout(loadTimer);
    current = valid ? id : null;
    // Removing the old iframe destroys its WebRTC peer, including pending retries.
    screen.replaceChildren();
    retry.disabled = !valid;
    overview.hidden = !valid;
    status.className = '';
    document.getElementById('current-title').textContent = valid ? `摄像头 ${id}` : '选择一个摄像头';
    document.getElementById('selection-label').textContent = valid ? `独立信号 / ${id}` : '未选择';
    document.title = valid ? `摄像头 ${id} · OntoTwin Nexus` : '监控总览 · OntoTwin Nexus';
    channels.querySelectorAll('a').forEach(link => {
      const selected = link.dataset.cameraId === current;
      link.setAttribute('aria-current', String(selected));
      link.querySelector('span').textContent = selected ? '当前选择' : '点击播放';
    });
    if (pushHistory) {
      const url = new URL(location.href);
      url.searchParams.delete('instance_id');
      url.searchParams.delete('camera_id');
      if (valid) url.searchParams.set('camera_id', id);
      history.pushState(null, '', url);
    }
    if (!valid) {
      screen.append(empty.cloneNode(true));
      status.textContent = id ? '摄像头编号无效，请选择 17–30。' : '尚未连接视频流';
      if (id) status.className = 'warning';
      return;
    }
    status.textContent = '正在打开播放器，首次连接需数秒…';
    const frame = document.createElement('iframe');
    frame.id = 'stream-player';
    frame.setAttribute('data-ontotwin-interactive', 'video');
    frame.title = `摄像头 ${id} 测试视频`;
    frame.allow = 'autoplay; fullscreen';
    frame.allowFullscreen = true;
    frame.referrerPolicy = 'no-referrer';
    frame.src = `${gateway}/${id}?autoplay=true&muted=true&controls=true`;
    frame.addEventListener('load', () => {
      if (token !== generation) return;
      clearTimeout(loadTimer);
      // Cross-origin load is not proof of media reception. Don't report "online".
      status.textContent = '已打开播放器；连接状态见画面。黑屏或报错可重新连接。';
    });
    screen.append(frame);
    loadTimer = setTimeout(() => {
      if (token === generation) {
        status.className = 'warning';
        status.textContent = '播放器响应较慢，请检查本机测试服务后重新连接。';
      }
    }, 20000);
  }
  document.getElementById('close-viewer').addEventListener('click', () => {
    // Stop the stream while keeping the channel menu available to reopen it.
    select(null, true);
    viewer.hidden = true;
    channels.querySelector('a')?.focus({ preventScroll: true });
  });
  function readUrl() { select(new URLSearchParams(location.search).get('camera_id')); }
  retry.addEventListener('click', () => { if (current) select(current); });
  overview.addEventListener('click', event => { event.preventDefault(); select(null, true); });
  window.addEventListener('popstate', readUrl);
  window.addEventListener('pagehide', () => { ++generation; clearTimeout(loadTimer); screen.replaceChildren(); });
  window.addEventListener('pageshow', event => { if (event.persisted) readUrl(); });
  readUrl();
})();
