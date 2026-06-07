#!/usr/bin/env bash
# Launch the ReflexOS robot MCP server on the real SO-101 follower, exposed via the
# reflexos.tedi.studio cloudflared tunnel, mirroring logs to outputs/server.log.
#
# Run from a CAMERA-AUTHORIZED terminal (e.g. the Codex terminal) so the camera
# (index 0) initializes. For motion-only (no camera), set REFLEXOS_CAMERA=-1.
#
#   bash scripts/run_robot.sh
#
# Env overrides: REFLEXOS_PORT, REFLEXOS_CAMERA, REFLEXOS_HTTP_PORT, REFLEXOS_PUBLIC_HOST
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p outputs
export PYTHONUNBUFFERED=1

# Kill any stale reflexos.server still holding the port, so a fresh build never gets
# shadowed by an old process bound to :8000. (Matches the python process argv, not
# this launcher.)
if pkill -f "reflexos\.server" 2>/dev/null; then
  echo "Stopped a previous reflexos.server instance"
  sleep 1
fi

PORT="${REFLEXOS_PORT:-/dev/tty.usbmodem5A7C1215751}"
CAM="${REFLEXOS_CAMERA:-0}"            # wrist (eye-in-hand) camera; -1 = motion-only
SCENE_CAM="${REFLEXOS_SCENE_CAMERA:-1}"  # distant/3rd-person camera; -1 = disable
HTTP_PORT="${REFLEXOS_HTTP_PORT:-8000}"
PUBLIC_HOST="${REFLEXOS_PUBLIC_HOST:-reflexos.tedi.studio}"

echo "Launching reflexos-robot: port=$PORT wrist_cam=$CAM scene_cam=$SCENE_CAM http=127.0.0.1:$HTTP_PORT public=$PUBLIC_HOST"
echo "Logs mirrored to outputs/server.log"
# Prefer the existing venv's interpreter so launching never needs the network.
# (`uv run` re-resolves/builds the project — which fails offline, e.g. at the
# hackathon venue. The venv already has mcp + lerobot + placo installed.)
if [ -x ".venv/bin/python" ]; then
  PYRUN=(.venv/bin/python)
else
  # Fall back to uv but skip the project sync/build so it stays offline-safe.
  PYRUN=(uv run --no-sync --extra server --extra robot --extra kinematics python)
fi
"${PYRUN[@]}" -u -m reflexos.server \
  --backend so101 \
  --port "$PORT" \
  --id reflexos_follower \
  --camera-index "$CAM" \
  --scene-camera-index "$SCENE_CAM" \
  --transport http \
  --host 127.0.0.1 \
  --http-port "$HTTP_PORT" \
  --public-host "$PUBLIC_HOST" \
  2>&1 | tee outputs/server.log
