"""REST + WebSocket bridge — streams live robot joint positions to the browser.

Read-only: never sends commands to the robot.

  GET  /state   → current joints + scene snapshot
  WS   /events  → live joint stream at ~10 Hz

Run with:
  python3 -m reflexos.rest_server [--backend sim|so101] [--port /dev/tty...] [--http-port 8080]
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ── ensure the cygnus package is importable regardless of cwd ──────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from reflexos.robot import build_backend
from reflexos.robot.base import RobotBackend

log = logging.getLogger("reflexos.rest_server")

# ── app ────────────────────────────────────────────────────────────────────
app = FastAPI(title="ReflexOS REST Bridge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── shared state ───────────────────────────────────────────────────────────
_robot: RobotBackend | None = None
_ws_clients: set[WebSocket] = set()


# ── helpers ────────────────────────────────────────────────────────────────
def _strip_pos(raw: dict[str, float]) -> dict[str, float]:
    """'shoulder_pan.pos' → 'shoulder_pan'  (frontend joint key format)."""
    return {(k[:-4] if k.endswith(".pos") else k): v for k, v in raw.items()}


def _obs_payload(obs) -> dict:
    scene = dict(obs.scene)
    return {
        "joints": _strip_pos(obs.joints),
        "scene": {
            "cube_zone": scene.get("cube_zone") or "A",
            "holding": bool(scene.get("holding", False) or obs.grasped),
            "cube_in_bin": bool(scene.get("cube_in_bin", False)),
        },
    }


async def _broadcast(payload: dict) -> None:
    if not _ws_clients:
        return
    msg = json.dumps(payload)
    dead: set[WebSocket] = set()
    for ws in _ws_clients.copy():
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


# ── state broadcaster (10 Hz) ──────────────────────────────────────────────
async def _state_broadcaster() -> None:
    loop = asyncio.get_event_loop()
    while True:
        try:
            if _robot and _ws_clients:
                obs = await loop.run_in_executor(None, _robot.get_observation)
                await _broadcast(_obs_payload(obs))
        except Exception as exc:
            log.warning("broadcaster error: %s", exc)
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def _startup() -> None:
    asyncio.create_task(_state_broadcaster())


# ── REST endpoints ─────────────────────────────────────────────────────────
@app.get("/state")
async def state_endpoint():
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.get_observation)
    return _obs_payload(obs)


@app.websocket("/events")
async def events_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    # send current state immediately on connect
    loop = asyncio.get_event_loop()
    try:
        obs = await loop.run_in_executor(None, _robot.get_observation)
        await ws.send_text(json.dumps(_obs_payload(obs)))
    except Exception:
        pass
    try:
        while True:
            # keep connection alive; the broadcaster sends updates
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_clients.discard(ws)



# ── static frontend (built with `npm run build` in live_simulation/) ───────
# The dist/ folder is relative to this file's grandparent (cygnus/../live_simulation/dist).
_DIST_DIR = Path(__file__).parent.parent / "live-robot-demo" / "dist"


def _mount_frontend() -> None:
    """Mount the built frontend if it exists; adds a catch-all for the SPA router."""
    if not _DIST_DIR.exists():
        log.warning("No built frontend found at %s — API-only mode. Run: cd live_simulation && npm run build", _DIST_DIR)
        return

    # Serve assets (JS/CSS/etc.) under /assets
    assets_dir = _DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # SPA catch-all: any path that isn't an API route → serve index.html
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        index = _DIST_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "frontend not built"}

    log.info("Serving built frontend from %s", _DIST_DIR)


# ── entry point ────────────────────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="ReflexOS REST bridge server")
    parser.add_argument("--backend", default="sim", choices=["sim", "so101"],
                        help="'sim' (no hardware) or 'so101' (real arm)")
    parser.add_argument("--port", default="", help="Serial port for so101")
    parser.add_argument("--id", default="reflexos_follower", help="Calibration ID for so101")
    parser.add_argument("--camera-index", type=int, default=-1)
    parser.add_argument("--http-port", type=int, default=8080, help="HTTP port for this server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--no-frontend", action="store_true",
                        help="Skip serving the built frontend (API-only)")
    args = parser.parse_args()

    global _robot
    if args.backend == "so101":
        if not args.port:
            parser.error("--port required for so101 backend")
        _robot = build_backend("so101", port=args.port, id=args.id, camera_index=args.camera_index)
    else:
        _robot = build_backend("sim")
    _robot.connect()

    if not args.no_frontend:
        _mount_frontend()

    print(f"\n[reflexos] backend={args.backend}  server=http://localhost:{args.http_port}")
    if _DIST_DIR.exists():
        print(f"[reflexos] Website:  http://localhost:{args.http_port}/")
        print(f"[reflexos] Share the cloudflared URL once the tunnel is up.\n")
    uvicorn.run(app, host=args.host, port=args.http_port, log_level="info")


if __name__ == "__main__":
    main()
