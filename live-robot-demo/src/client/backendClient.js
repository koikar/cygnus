// When VITE_BACKEND_URL is set (local dev), use it explicitly.
// When empty/absent, use same-origin so the built frontend served by the
// bridge over a public tunnel just works without any config change.
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? '';

function apiUrl(path) {
  return BACKEND_URL ? `${BACKEND_URL}${path}` : path;
}

function buildWsUrl() {
  if (BACKEND_URL) return BACKEND_URL.replace(/^http/, 'ws') + '/events';
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}/events`;
}

export function hasBackend() {
  return true; // always attempt; health check decides live vs mock
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(apiUrl('/state'), { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function getState() {
  const res = await fetch(apiUrl('/state'));
  if (!res.ok) throw new Error('GET /state failed');
  return res.json();
}

export async function postDemoRun(payload = {}) {
  const res = await fetch(apiUrl('/demo/run'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('POST /demo/run failed');
  return res.json();
}

export async function postInjectFailure(failureType) {
  const res = await fetch(apiUrl('/demo/inject-failure'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: failureType }),
  });
  if (!res.ok) throw new Error('POST /demo/inject-failure failed');
  return res.json();
}

export async function postReplay() {
  const res = await fetch(apiUrl('/demo/replay'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('POST /demo/replay failed');
  return res.json();
}

export async function postReset() {
  const res = await fetch(apiUrl('/demo/reset'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('POST /demo/reset failed');
  return res.json();
}

export function connectWebSocket(onEvent, onOpen, onClose) {
  let ws;
  try {
    ws = new WebSocket(buildWsUrl());
    ws.onopen = () => { if (onOpen) onOpen(); };
    ws.onclose = () => { if (onClose) onClose(); };
    ws.onerror = () => { if (onClose) onClose(); };
    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (onEvent) onEvent(payload);
      } catch {
        // ignore malformed payloads
      }
    };
  } catch {
    return null;
  }
  return ws;
}
