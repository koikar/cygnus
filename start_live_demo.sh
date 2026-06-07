#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# ReflexOS Live Demo  — one command to share the robot with the world
#
# Usage:
#   ./start_live_demo.sh                         # simulator (no hardware)
#   ./start_live_demo.sh --backend so101 --port /dev/tty.usbmodemXXXX
#
# What it does:
#   1. Starts the Python bridge (robot → REST/WebSocket on port 8080)
#   2. Opens a cloudflared tunnel → public HTTPS URL
#   3. Prints the URL — share it and anyone can watch the 3D live view
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_PORT=8080
BACKEND_ARGS=("$@")

# ── 1. build / verify frontend ────────────────────────────────────────────────
DIST="$SCRIPT_DIR/live-robot-demo/dist"
if [ ! -f "$DIST/index.html" ]; then
  echo "[setup] Building frontend…"
  cd "$SCRIPT_DIR/live-robot-demo"
  VITE_BACKEND_URL= npm run build
  cd "$SCRIPT_DIR"
fi

# ── 2. start the Python bridge ────────────────────────────────────────────────
echo "[bridge] Starting on port $BRIDGE_PORT …"
cd "$SCRIPT_DIR"
python3 -m reflexos.rest_server --http-port "$BRIDGE_PORT" "${BACKEND_ARGS[@]}" \
  > /tmp/reflexos_bridge.log 2>&1 &
BRIDGE_PID=$!
echo "[bridge] PID $BRIDGE_PID"

# wait until the bridge is accepting connections
for i in $(seq 1 20); do
  if curl -sf "http://localhost:$BRIDGE_PORT/state" > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -sf "http://localhost:$BRIDGE_PORT/state" > /dev/null 2>&1; then
  echo "[bridge] ERROR — bridge did not start. Check /tmp/reflexos_bridge.log"
  kill $BRIDGE_PID 2>/dev/null
  exit 1
fi
echo "[bridge] ✓ up"

# ── 3. cloudflared tunnel ─────────────────────────────────────────────────────
echo "[tunnel] Opening public tunnel…"
TUNNEL_LOG=/tmp/reflexos_tunnel.log
cloudflared tunnel --url "http://localhost:$BRIDGE_PORT" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# parse the public URL from cloudflared output (appears within ~5 s)
PUBLIC_URL=""
for i in $(seq 1 30); do
  PUBLIC_URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
  [ -n "$PUBLIC_URL" ] && break
  sleep 0.5
done

if [ -z "$PUBLIC_URL" ]; then
  echo "[tunnel] Could not get public URL — check $TUNNEL_LOG"
  PUBLIC_URL="(tunnel URL not found — check $TUNNEL_LOG)"
fi

# ── 4. done ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ReflexOS is LIVE                                        ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  🌐 Public URL:  $PUBLIC_URL"
echo "║  💻 Local URL:   http://localhost:$BRIDGE_PORT/"
echo "║                                                          ║"
echo "║  Share the public URL — anyone can open it and watch     ║"
echo "║  the 3D simulation mirror your real robot live.          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop everything."

cleanup() {
  echo ""
  echo "[stop] Shutting down…"
  kill $BRIDGE_PID 2>/dev/null || true
  kill $TUNNEL_PID 2>/dev/null || true
}
trap cleanup INT TERM

wait $BRIDGE_PID
