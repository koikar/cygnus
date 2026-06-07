const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export function hasBackend() {
  return Boolean(BACKEND_URL);
}

export async function checkBackendHealth() {
  if (!BACKEND_URL) return false;
  try {
    const res = await fetch(`${BACKEND_URL}/state`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function getState() {
  const res = await fetch(`${BACKEND_URL}/state`);
  if (!res.ok) throw new Error('GET /state failed');
  return res.json();
}

export async function postDemoRun(payload = {}) {
  const res = await fetch(`${BACKEND_URL}/demo/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('POST /demo/run failed');
  return res.json();
}

export async function postInjectFailure(failureType) {
  const res = await fetch(`${BACKEND_URL}/demo/inject-failure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: failureType }),
  });
  if (!res.ok) throw new Error('POST /demo/inject-failure failed');
  return res.json();
}

export async function postReplay() {
  const res = await fetch(`${BACKEND_URL}/demo/replay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('POST /demo/replay failed');
  return res.json();
}

export async function postReset() {
  const res = await fetch(`${BACKEND_URL}/demo/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('POST /demo/reset failed');
  return res.json();
}

export function connectWebSocket(onEvent, onOpen, onClose) {
  if (!BACKEND_URL) return null;
  const wsUrl = BACKEND_URL.replace(/^http/, 'ws') + '/events';
  let ws;
  try {
    ws = new WebSocket(wsUrl);
    ws.onopen = () => { if (onOpen) onOpen(); };
    ws.onclose = () => { if (onClose) onClose(); };
    ws.onerror = () => { if (onClose) onClose(); };
    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (onEvent) onEvent(payload);
      } catch {
        // ignore invalid payloads
      }
    };
  } catch {
    return null;
  }
  return ws;
}
