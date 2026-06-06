"""Adaptive, self-correcting grab over the LOCAL MCP server.

Static named poses (``paper_pos_N``) are open-loop: they drive to a fixed joint
target regardless of where the cube actually is. As soon as the cube drifts a
few millimetres the grab misses, because the SO-101 grab window is only ~+/-2 deg
of ``shoulder_pan`` (a couple of mm) wide. This module closes the loop with the
wrist camera so the grab reacts to the cube's *actual* position and retries.

The loop (perceive -> decide -> act -> verify -> recover):

  1. HOVER open-claw a little above the nominal grab pose (no contact).
  2. LOOK with the wrist cam, find the cube (largest compact saturated blob),
     measure its horizontal offset from the jaw grasp column.
  3. CORRECT shoulder_pan toward the cube and re-look. Repeat until centred.
     (All correction happens at hover height, so the cube is never nudged.)
  4. DESCEND straight down (same pan) and CLOSE.
  5. VERIFY by lifting and checking the cube rode up with the claw
     (differential: a held cube stays put in the wrist frame because the camera
     moves with it; a missed cube recedes/shrinks). gripper.pos is NOT used as
     the gate -- for a small cube, empty-close ~= held-close, so it is ambiguous.
  6. RECOVER: if empty, open, widen the pan search, and retry up to ``max_tries``.

Calibration constants below were measured live on 2026-06-06 (cube drifted from
pan 18.5 to a grab at pan 21): increasing pan moves the jaws toward a cube that
sits to the lower-x ("left") side of the wrist frame, ~36 px per degree.

Usage:
  python scripts/adaptive_grab.py grab paper_pos_2      # adaptive grab at a saved position
  python scripts/adaptive_grab.py grab paper_pos_2 --dry  # hover+measure only, no contact
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://127.0.0.1:8000/mcp"
OUT = Path("outputs/adaptive")

# --- live-measured wrist-camera / pan calibration (640x480 frame) ------------
PX_PER_DEG = 36.0          # cube travels ~36 px horizontally per deg of shoulder_pan
JAW_TARGET_CX = 300.0      # image column the cube must reach to sit in the jaw gap
ALIGN_TOL_PX = 28.0        # "centred enough" to descend
MAX_PAN_STEP = 5.0         # clamp per-correction pan move (deg)
HOVER_LIFT_DELTA = 12.0    # raise shoulder_lift this much above grab for a no-contact hover
GRIP_OPEN = 60
GRIP_CLOSE = 15
LIFT_DEG = 16.0            # verify lift (shoulder_lift -=) after close


def _payloads(result):
    out = []
    for b in result.content:
        if getattr(b, "type", None) == "text":
            try:
                out.append(("json", json.loads(b.text)))
            except json.JSONDecodeError:
                out.append(("text", b.text))
        elif getattr(b, "type", None) == "image":
            out.append(("image", base64.b64decode(b.data)))
    return out


def _json(result):
    for k, v in _payloads(result):
        if k == "json":
            return v
    return {}


def _save_img(result, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for k, v in _payloads(result):
        if k == "image":
            (OUT / f"{name}.jpg").write_bytes(v)
            return OUT / f"{name}.jpg"
    return None


def _cube_blob(detection_result):
    """Pick the cube = largest *compact* blob (reject elongated tape/grid lines)."""
    best = None
    for d in detection_result.get("detections", []):
        bb = d.get("bbox", {})
        w, h = bb.get("width", 1), bb.get("height", 1)
        aspect = max(w, h) / max(1, min(w, h))
        if aspect > 3.0:          # long thin line -> tape/grid, not the cube
            continue
        if best is None or d["area_px"] > best["area_px"]:
            best = d
    return best


async def _state(s):
    return _json(await s.call_tool("get_state", {}))["joints"]


async def grab(name: str, dry: bool = False, max_tries: int = 3):
    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            # nominal grab pose = the position skill's move_to target
            skill = _json(await s.call_tool("run_skill", {"name": name, "dry_run": True})) \
                if False else None
            base = json.load(open(f"skills/{name}.json"))
            grab_pose = next(st["args"]["target"] for st in base["steps"] if st["tool"] == "move_to")
            grab_pose = {k: float(v) for k, v in grab_pose.items()}
            pan = grab_pose["shoulder_pan.pos"]

            for attempt in range(1, max_tries + 1):
                # 1-3) hover + correct pan from vision (no contact)
                for it in range(4):
                    hover = dict(grab_pose, **{"shoulder_pan.pos": pan})
                    hover["shoulder_lift.pos"] -= HOVER_LIFT_DELTA
                    await s.call_tool("set_gripper", {"position": GRIP_OPEN})
                    await s.call_tool("move_to", {"target": hover})
                    await s.call_tool("wait_until_settled", {"timeout": 1.0})
                    det = _json(await s.call_tool("detect_colored_blocks", {"camera": "wrist", "max_results": 15}))
                    _save_img(await s.call_tool("look", {"camera": "wrist", "max_width": 512}),
                              f"{name}_try{attempt}_hover{it}")
                    cube = _cube_blob(det)
                    if not cube:
                        print(f"[try{attempt} it{it}] no cube blob; holding pan={pan:.1f}")
                        break
                    cx = cube["center"]["x"]
                    err_px = JAW_TARGET_CX - cx          # cube left of target -> positive -> +pan
                    print(f"[try{attempt} it{it}] cube cx={cx} err={err_px:+.0f}px pan={pan:.1f}")
                    if abs(err_px) <= ALIGN_TOL_PX:
                        break
                    step = max(-MAX_PAN_STEP, min(MAX_PAN_STEP, err_px / PX_PER_DEG))
                    pan += step
                if dry:
                    print(f"[dry] would grab at pan={pan:.1f}")
                    return

                # 4) descend straight + close
                await s.call_tool("move_to", {"target": dict(grab_pose, **{"shoulder_pan.pos": pan})})
                await s.call_tool("wait_until_settled", {"timeout": 1.0})
                det_lo = _json(await s.call_tool("detect_colored_blocks", {"camera": "wrist"}))
                a0 = (_cube_blob(det_lo) or {}).get("area_px", 0)
                await s.call_tool("set_gripper", {"position": GRIP_CLOSE})
                await s.call_tool("wait_until_settled", {"timeout": 1.0})

                # 5) lift + verify (differential: held cube stays large in-frame)
                await s.call_tool("move_relative", {"delta": {"shoulder_lift.pos": -LIFT_DEG},
                                                    "tolerance": 1.5, "timeout": 3.0})
                await s.call_tool("wait_until_settled", {"timeout": 1.0})
                det_hi = _json(await s.call_tool("detect_colored_blocks", {"camera": "wrist"}))
                a1 = (_cube_blob(det_hi) or {}).get("area_px", 0)
                img = _save_img(await s.call_tool("look", {"camera": "wrist", "max_width": 512}),
                                f"{name}_try{attempt}_lift")
                held = a1 >= 0.6 * max(a0, 1) and a1 > 150
                print(f"[try{attempt}] grab area {a0:.0f}->{a1:.0f}  held={held}  img={img}")
                if held:
                    print(f"GRABBED at pan={pan:.1f} (try {attempt}). Verify image: {img}")
                    return {"held": True, "pan": pan, "tries": attempt, "image": str(img)}

                # 6) recover: open, widen search, retry
                await s.call_tool("set_gripper", {"position": GRIP_OPEN})
                pan += MAX_PAN_STEP * (1 if attempt % 2 else -1)
                print(f"[try{attempt}] missed; widening pan -> {pan:.1f}")
            print("ADAPTIVE GRAB FAILED after retries; human review needed.")
            return {"held": False, "tries": max_tries}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["grab"])
    ap.add_argument("position")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--max-tries", type=int, default=3)
    a = ap.parse_args()
    asyncio.run(grab(a.position, dry=a.dry, max_tries=a.max_tries))


if __name__ == "__main__":
    main()
