#!/usr/bin/env bash
# Launch the Cygnus robot MCP server on the real SO-101 follower, exposed via the
# cygnus.tedi.studio cloudflared tunnel, mirroring logs to outputs/server.log.
#
# Run from a CAMERA-AUTHORIZED terminal (e.g. the Codex terminal) so the camera
# (index 0) initializes. For motion-only (no camera), set CYGNUS_CAMERA=-1.
#
#   bash scripts/run_robot.sh
#
# Env overrides: CYGNUS_PORT, CYGNUS_CAMERA, CYGNUS_HTTP_PORT, CYGNUS_PUBLIC_HOST
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p outputs
export PYTHONUNBUFFERED=1

PORT="${CYGNUS_PORT:-/dev/tty.usbmodem5A7C1215751}"
CAM="${CYGNUS_CAMERA:-0}"            # wrist (eye-in-hand) camera; -1 = motion-only
SCENE_CAM="${CYGNUS_SCENE_CAMERA:-1}"  # distant/3rd-person camera; -1 = disable
HTTP_PORT="${CYGNUS_HTTP_PORT:-8000}"
PUBLIC_HOST="${CYGNUS_PUBLIC_HOST:-cygnus.tedi.studio}"

echo "Launching cygnus-robot: port=$PORT wrist_cam=$CAM scene_cam=$SCENE_CAM http=127.0.0.1:$HTTP_PORT public=$PUBLIC_HOST"
echo "Logs mirrored to outputs/server.log"
uv run python -u -m cygnus.server \
  --backend so101 \
  --port "$PORT" \
  --id cygnus_follower \
  --camera-index "$CAM" \
  --scene-camera-index "$SCENE_CAM" \
  --transport http \
  --host 127.0.0.1 \
  --http-port "$HTTP_PORT" \
  --public-host "$PUBLIC_HOST" \
  2>&1 | tee outputs/server.log
