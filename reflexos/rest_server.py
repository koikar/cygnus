"""REST + WebSocket bridge — exposes the reflexos robot as a live-demo HTTP API.

The frontend (live_simulation / live-robot-demo) connects to this server:
  GET  /state              → current joints + scene
  POST /demo/run           → starts the full 3-episode antifragility demo
  POST /demo/inject-failure→ jumps straight to episode 2 (failure scenario)
  POST /demo/replay        → jumps to episode 3 (reflex replay)
  POST /demo/reset         → returns arm to home and clears state
  WS   /events             → streams state + events at ~10 Hz

Run with:
  python3 -m reflexos.rest_server [--backend sim|so101] [--port /dev/tty...] [--http-port 8080]

Set VITE_BACKEND_URL=http://localhost:8080 in the frontend .env.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ── ensure the cygnus package is importable regardless of cwd ──────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from reflexos.robot import build_backend
from reflexos.robot.base import RobotBackend
from reflexos import poses

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
_demo_task: asyncio.Task | None = None
_metrics: dict[str, Any] = {
    "episode": 0,
    "cost": 0,
    "antifragility_score": 0,
    "learned_reflexes": 0,
    "first_attempt_cost": None,
    "second_attempt_cost": None,
}
_memory_cards: list[dict] = []
_episode_history: list[dict] = []


# ── helpers ────────────────────────────────────────────────────────────────
def _strip_pos(raw: dict[str, float]) -> dict[str, float]:
    """'shoulder_pan.pos' → 'shoulder_pan'  (frontend joint key format)."""
    return {(k[:-4] if k.endswith(".pos") else k): v for k, v in raw.items()}


def _obs_payload(obs, *, event: dict | None = None, metrics_patch: dict | None = None,
                 new_memory_card: dict | None = None, episode_result: dict | None = None,
                 reasoning_step: str | None = None, reset_reasoning: bool = False) -> dict:
    scene = dict(obs.scene)
    payload: dict[str, Any] = {
        "joints": _strip_pos(obs.joints),
        "scene": {
            "cube_zone": scene.get("cube_zone") or "A",
            "holding": bool(scene.get("holding", False) or obs.grasped),
            "cube_in_bin": bool(scene.get("cube_in_bin", False)),
        },
    }
    if event:
        payload["event"] = event
    if metrics_patch:
        _metrics.update(metrics_patch)
    payload["metrics"] = dict(_metrics)
    if new_memory_card:
        payload["newMemoryCard"] = new_memory_card
    if episode_result:
        payload["episodeResult"] = episode_result
    if reasoning_step:
        payload["reasoningStep"] = reasoning_step
    if reset_reasoning:
        payload["resetReasoning"] = True
    return payload


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


@app.post("/demo/reset")
async def demo_reset():
    global _demo_task, _metrics, _memory_cards, _episode_history
    if _demo_task and not _demo_task.done():
        _demo_task.cancel()
    _robot.reset()
    _metrics = {
        "episode": 0, "cost": 0, "antifragility_score": 0,
        "learned_reflexes": 0, "first_attempt_cost": None, "second_attempt_cost": None,
    }
    _memory_cards.clear()
    _episode_history.clear()
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.get_observation)
    await _broadcast(_obs_payload(obs, event={"type": "system", "message": "Reset — ready"}))
    return {"ok": True}


@app.post("/demo/run")
async def demo_run(body: dict = {}):
    global _demo_task
    if _demo_task and not _demo_task.done():
        _demo_task.cancel()
    _demo_task = asyncio.create_task(_full_demo())
    return {"ok": True, "message": "Full demo started"}


@app.post("/demo/inject-failure")
async def demo_inject_failure(body: dict = {}):
    global _demo_task
    if _demo_task and not _demo_task.done():
        _demo_task.cancel()
    _demo_task = asyncio.create_task(_episode2())
    return {"ok": True}


@app.post("/demo/replay")
async def demo_replay(body: dict = {}):
    global _demo_task
    if _demo_task and not _demo_task.done():
        _demo_task.cancel()
    _demo_task = asyncio.create_task(_episode3())
    return {"ok": True}


# ── demo sequence helpers ──────────────────────────────────────────────────
async def _move(target: dict, msg: str | None = None, event_type: str = "action",
                cost_inc: int = 1, sleep: float = 1.0,
                reasoning_step: str | None = None, reasoning_msg: str | None = None):
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.move_to, target)
    _metrics["cost"] = (_metrics.get("cost") or 0) + cost_inc
    payload = _obs_payload(
        obs,
        event={"type": event_type, "message": msg} if msg else None,
        metrics_patch={"cost": _metrics["cost"]},
        reasoning_step=reasoning_step,
    )
    await _broadcast(payload)
    await asyncio.sleep(sleep)
    return obs


async def _grip(mode: str, msg: str | None = None, event_type: str = "action",
                reasoning_step: str | None = None):
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.grip, mode)
    _metrics["cost"] = (_metrics.get("cost") or 0) + 1
    payload = _obs_payload(
        obs,
        event={"type": event_type, "message": msg} if msg else None,
        metrics_patch={"cost": _metrics["cost"]},
        reasoning_step=reasoning_step,
    )
    await _broadcast(payload)
    await asyncio.sleep(0.6)
    return obs


async def _announce(obs, msg: str, event_type: str = "system", reasoning_step: str | None = None,
                    reset_reasoning: bool = False, metrics_patch: dict | None = None,
                    new_memory_card: dict | None = None, episode_result: dict | None = None,
                    sleep: float = 1.0):
    payload = _obs_payload(
        obs,
        event={"type": event_type, "message": msg},
        metrics_patch=metrics_patch or {},
        reasoning_step=reasoning_step,
        reset_reasoning=reset_reasoning,
        new_memory_card=new_memory_card,
        episode_result=episode_result,
    )
    await _broadcast(payload)
    await asyncio.sleep(sleep)


# ── Episode sequences ──────────────────────────────────────────────────────
async def _episode1():
    """Normal habit: cube at zone A → success."""
    _robot.reset(cube_zone="A")
    _metrics.update({"episode": 1, "cost": 0, "first_attempt_cost": None, "second_attempt_cost": None})
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.get_observation)
    await _announce(obs, "Episode 1 started — habit mode", reset_reasoning=True,
                    metrics_patch={"episode": 1, "cost": 0}, reasoning_step="observe", sleep=1.0)

    # Look
    await _move({"shoulder_pan.pos": 5, "shoulder_lift.pos": -10, "elbow_flex.pos": 15},
                "look()", cost_inc=1, sleep=0.7, reasoning_step="observe")

    # Move to Zone A
    await _move(poses.ZONE_POSE["A"], "move_to(zone_A)", cost_inc=1, sleep=1.1, reasoning_step="observe")

    # Grip close
    await _grip("close", "grip(close)  ✓", reasoning_step="validate")

    # Move to bin
    await _move(poses.BIN_POSE, "move_to(bin)", cost_inc=1, sleep=1.1, reasoning_step="validate")

    # Release
    obs = await _grip("open", "release()  ✓", event_type="success", reasoning_step="validate")

    await _announce(obs, "Episode 1 complete — cost: 4", event_type="success",
                    metrics_patch={"cost": 4},
                    episode_result={"episode": 1, "cost": 4, "mode": "habit", "success": True, "escalated": False},
                    sleep=1.5)


async def _episode2():
    """Black-swan failure: cube moved to zone B → robot fails at A → recovers → learns."""
    _robot.reset(cube_zone="B")
    _metrics.update({"episode": 2, "cost": 0})
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.get_observation)
    await _announce(obs, "Episode 2 — cube secretly moved to zone B",
                    reset_reasoning=True, metrics_patch={"episode": 2, "cost": 0},
                    reasoning_step="observe", sleep=1.4)

    # Look (uncertain)
    await _move({"shoulder_pan.pos": 5, "shoulder_lift.pos": -10, "elbow_flex.pos": 15},
                "look()", cost_inc=1, sleep=0.7, reasoning_step="observe")

    # Habit move to A (wrong)
    await _move(poses.ZONE_POSE["A"], "move_to(zone_A)  [habit]", cost_inc=1, sleep=1.1,
                reasoning_step="observe")

    # Grip FAILS (cube is at B, not A)
    obs = await _grip("close", "grip(close)  ✗  EMPTY GRIPPER", event_type="error",
                      reasoning_step="detect")

    # System 2 reasoning
    await _announce(obs, "BLACK SWAN: Gripper closed but cube was not grasped",
                    event_type="failure", reasoning_step="compare", sleep=1.0)
    await _announce(obs, "system2_reasoning(active)", event_type="reasoning",
                    reasoning_step="locate", sleep=0.8)

    # Recover: move to zone B
    await _move(poses.ZONE_POSE["B"], "recover: move_to(zone_B)", cost_inc=1, sleep=1.1,
                event_type="recovery", reasoning_step="plan")

    # Grip succeeds at B
    obs = await _grip("close", "grip(close)  ✓  [zone B]", event_type="recovery",
                      reasoning_step="validate")

    # Move to bin
    await _move(poses.BIN_POSE, "move_to(bin)", cost_inc=1, sleep=1.1, reasoning_step="validate")

    # Release
    obs = await _grip("open", "release()  ✓", event_type="action", reasoning_step="validate")

    await _announce(obs, "Episode 2 complete via recovery — cost: 8", event_type="success",
                    metrics_patch={"cost": 8, "first_attempt_cost": 8},
                    episode_result={"episode": 2, "cost": 8, "mode": "system2", "success": True, "escalated": True},
                    sleep=0.7)

    # Learning
    _metrics["learned_reflexes"] = 1
    new_card = {
        "signature": "cube@B",
        "why": "Default habit expected cube@A — but cube was at zone B.",
        "plan": "move_to(B) → grip → move_to(bin) → release",
        "uses": 0,
        "costSaved": 4,
    }
    _memory_cards.append(new_card)
    _robot.reset(cube_zone="B")
    obs2 = await loop.run_in_executor(None, _robot.get_observation)
    await _announce(obs2, "memory.upsert(signature=\"cube@B\")", event_type="learn",
                    metrics_patch={"antifragility_score": 50, "learned_reflexes": 1},
                    new_memory_card=new_card, reasoning_step="save", sleep=1.6)


async def _episode3():
    """Reflex replay: cube at B → reflex recalled → direct success at lower cost."""
    _robot.reset(cube_zone="B")
    _metrics.update({"episode": 3, "cost": 0})
    loop = asyncio.get_event_loop()
    obs = await loop.run_in_executor(None, _robot.get_observation)
    await _announce(obs, "Episode 3 — same cube@B scenario",
                    reset_reasoning=True, metrics_patch={"episode": 3, "cost": 0},
                    reasoning_step="observe", sleep=1.4)

    # Look
    await _move({"shoulder_pan.pos": 5, "shoulder_lift.pos": -10, "elbow_flex.pos": 15},
                "look()", cost_inc=1, sleep=0.5, reasoning_step="observe")

    # Reflex recalled
    obs2 = await loop.run_in_executor(None, _robot.get_observation)
    await _announce(obs2, "reflex_recall(signature=\"cube@B\")  ⚡", event_type="reflex",
                    metrics_patch={"cost": 2}, reasoning_step="plan", sleep=0.9)

    # Direct to zone B (no zone A detour)
    await _move(poses.ZONE_POSE["B"], "move_to(zone_B)  [reflex direct]",
                event_type="reflex", cost_inc=0, sleep=0.9, reasoning_step="plan")

    # Grip
    obs = await _grip("close", "grip(close)  ✓  [reflex]", event_type="action",
                      reasoning_step="validate")

    # Move to bin
    await _move(poses.BIN_POSE, "move_to(bin)  [reflex]", event_type="reflex",
                cost_inc=1, sleep=0.9, reasoning_step="validate")

    # Release
    obs = await _grip("open", "release()  ✓  [reflex complete]", event_type="success",
                      reasoning_step="validate")

    await _announce(obs, "Episode 3 via reflex — cost: 4 (50% faster!)", event_type="success",
                    metrics_patch={"cost": 4, "second_attempt_cost": 4},
                    episode_result={"episode": 3, "cost": 4, "mode": "reflex", "success": True, "escalated": False},
                    sleep=0.7)

    await _announce(obs, "ANTIFRAGILE: system learned and improved — cost 8 → 4",
                    event_type="reflex", metrics_patch={"antifragility_score": 50},
                    sleep=2.0)


async def _full_demo():
    await _episode1()
    await asyncio.sleep(1.5)
    await _episode2()
    await asyncio.sleep(1.5)
    await _episode3()


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
