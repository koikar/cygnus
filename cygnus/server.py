"""The robot MCP server — the arm's body exposed as MCP tools.

Any MCP-speaking agent (Codex, Claude, or a hosted tedi) can operate the arm
through ``look`` / ``get_state`` / ``move_to`` / ``grip`` / ``home``. The active
body is chosen by ``--backend sim|so101``; safety guardrails are enforced on
every ``move_to`` regardless of caller. On real hardware the body has two USB
channels: Feetech serial for motion, and an OpenCV/UVC camera for vision.

Transport (``--transport``):
  * ``stdio`` — the MCP client spawns this as a local subprocess. Use when the
    agent runs on the SAME machine the arm is plugged into.
  * ``http``  — streamable HTTP server on ``--host:--port``. Use when a remote
    agent (e.g. a hosted tedi) must reach the arm over the network; expose it
    with a tunnel (cloudflared/ngrok) and add that URL to the tedi.

    # local agent on this laptop:
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --camera-index 1 --transport stdio
    # reachable by a remote tedi:
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --camera-index 1 --transport http --host 0.0.0.0 --http-port 8000
"""

from __future__ import annotations

import argparse
import json
import time

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ToolAnnotations

from .robot import build_backend
from .robot.base import RobotBackend
from .safety import JOINT_LIMITS, clamp_action, sanitize_call
from .types import Observation

mcp = FastMCP("cygnus-robot")

# MCP annotations are read by the consuming platform (e.g. a tedi's catalog scan)
# to drive approval UX: read-only perception needs no gate; actuation moves
# physical hardware and should be gated by the client where supported.
_READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
_ACTUATE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True
)
# Writes a skill file but moves no hardware — no approval gate needed.
_WRITE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)

# Set by main(); the tools operate this body.
_robot: RobotBackend | None = None


def _backend() -> RobotBackend:
    if _robot is None:
        raise RuntimeError("robot backend not initialized; run via `python -m cygnus.server`")
    return _robot


def _obs_to_dict(obs: Observation) -> dict:
    """MCP-serializable view of an observation (raw frames omitted; names listed)."""
    cameras = sorted(obs.frames) if obs.frames else (["front"] if obs.frame is not None else [])
    return {
        "joints": obs.joints,
        "scene": obs.scene,
        "grasped": obs.grasped,
        "cameras": cameras,
        "note": obs.note,
    }


def _motion_status(
    obs: Observation,
    target: dict[str, float] | None = None,
    *,
    tolerance: float = 2.0,
) -> dict:
    errors = {}
    reached = None
    if target:
        errors = {
            key: obs.joints.get(key, float("nan")) - value
            for key, value in target.items()
            if key in obs.joints
        }
        reached = all(abs(error) <= tolerance for error in errors.values())
    return {
        "target_reached": reached,
        "tolerance": tolerance,
        "errors": errors,
    }


def _wait_for_motion(
    target: dict[str, float] | None = None,
    *,
    timeout: float = 2.0,
    tolerance: float = 2.0,
    stable_tolerance: float = 0.75,
    stable_samples: int = 3,
    poll_interval: float = 0.08,
) -> tuple[Observation, dict]:
    """Poll observations until a target is reached, or a free-running pose settles."""
    deadline = time.monotonic() + max(0.0, timeout)
    backend = _backend()
    previous: dict[str, float] | None = None
    stable_count = 0
    obs = backend.get_observation()
    polls = 0

    while True:
        polls += 1
        status = _motion_status(obs, target, tolerance=tolerance)
        if target and status["target_reached"]:
            status.update({"settled": True, "reason": "target_reached", "polls": polls})
            return obs, status

        if previous is not None:
            common = [key for key in obs.joints if key in previous]
            max_delta = max(
                (abs(obs.joints[key] - previous[key]) for key in common),
                default=0.0,
            )
            stable_count = stable_count + 1 if max_delta <= stable_tolerance else 0
        else:
            max_delta = None

        if not target and stable_count >= stable_samples:
            status.update(
                {
                    "settled": True,
                    "reason": "pose_stable",
                    "polls": polls,
                    "max_delta": max_delta,
                    "stable_samples": stable_count,
                }
            )
            return obs, status

        if time.monotonic() >= deadline:
            status.update(
                {
                    "settled": stable_count >= stable_samples,
                    "reason": "timeout",
                    "polls": polls,
                    "max_delta": max_delta,
                    "stable_samples": stable_count,
                }
            )
            return obs, status

        previous = dict(obs.joints)
        time.sleep(poll_interval)
        obs = backend.get_observation()


def _obs_with_motion(obs: Observation, motion: dict, target: dict[str, float] | None = None) -> dict:
    result = _obs_to_dict(obs)
    if target is not None:
        result["target"] = target
    result["motion"] = motion
    return result


def _move_to(
    target: dict[str, float],
    *,
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    safe_target = clamp_action(target)
    obs = _backend().move_to(safe_target)
    if wait:
        obs, motion = _wait_for_motion(safe_target, timeout=timeout, tolerance=tolerance)
    else:
        motion = _motion_status(obs, safe_target, tolerance=tolerance) | {
            "settled": False,
            "reason": "not_waited",
            "polls": 0,
        }
    return _obs_with_motion(obs, motion, safe_target)


def _set_gripper(
    position: float,
    *,
    wait: bool = True,
    timeout: float = 1.5,
    tolerance: float = 2.0,
) -> dict:
    return _move_to(
        {"gripper.pos": position},
        wait=wait,
        timeout=timeout,
        tolerance=tolerance,
    )


def _grip_mode(
    mode: str,
    *,
    wait: bool = True,
    timeout: float = 1.5,
    tolerance: float = 2.0,
) -> dict:
    from . import poses

    if mode not in {"open", "close"}:
        raise ValueError(f"grip mode must be 'open' or 'close', got {mode!r}")
    value = poses.CLOSED_GRIP if mode == "close" else poses.OPEN_GRIP
    target = {"gripper.pos": value}
    obs = _backend().grip(mode)
    if wait:
        obs, motion = _wait_for_motion(target, timeout=timeout, tolerance=tolerance)
    else:
        motion = _motion_status(obs, target, tolerance=tolerance) | {
            "settled": False,
            "reason": "not_waited",
            "polls": 0,
        }
    return _obs_with_motion(obs, motion, target)


@mcp.tool(annotations=_READ_ONLY)
def get_capabilities() -> dict:
    """Return the robot MCP contract and safety envelope."""
    return {
        "name": "cygnus-robot",
        "backend": _backend().name,
        "tools": {
            "look": "Capture the camera image plus current robot state.",
            "get_state": "Return joint positions and structured scene state.",
            "get_robot_model": "Return joints, limits, presets, cameras, and current state.",
            "move_to": "Move toward safe joint-space targets; targets are clamped.",
            "move_relative": "Nudge joints relative to the current pose.",
            "set_gripper": "Command a numeric gripper position.",
            "grip": "Open or close the gripper.",
            "wait_until_settled": "Poll until the observed pose stops changing.",
            "run_sequence": "Execute an atomic multi-step tool sequence.",
            "home": "Return to the neutral safe pose.",
        },
        "hardware_channels": {
            "motion": "SO-101 follower / Feetech serial bus over USB",
            "vision": "OpenCV/UVC camera over USB",
        },
        "safety": {
            "move_to_clamped": True,
            "actuation_tools_destructive": True,
            "e_stop": "Ctrl+C the server or remove robot power.",
        },
    }


@mcp.tool(annotations=_READ_ONLY)
def get_robot_model() -> dict:
    """Return the agent-facing body schema: joints, limits, presets, and state."""
    from . import poses

    state = _obs_to_dict(_backend().get_observation())
    return {
        "backend": _backend().name,
        "joint_order": list(poses.JOINTS),
        "joints": {
            key: {
                "name": key.removesuffix(".pos"),
                "position_key": key,
                "limits": {"min": lo, "max": hi},
                "current": state["joints"].get(key),
            }
            for key, (lo, hi) in JOINT_LIMITS.items()
        },
        "gripper": {
            "position_key": "gripper.pos",
            "open_preset": poses.OPEN_GRIP,
            "closed_preset": poses.CLOSED_GRIP,
            "note": "Use set_gripper(position) to sweep the calibrated numeric range.",
        },
        "named_poses": {
            "home": poses.HOME,
            "bin": poses.BIN_POSE,
            "zones": poses.ZONE_POSE,
        },
        "cameras": state["cameras"],
        "state": state,
    }


@mcp.tool(annotations=_READ_ONLY)
def get_state() -> dict:
    """Return current joint positions and the structured scene."""
    return _obs_to_dict(_backend().get_observation())


def _encode_jpeg(frame, max_width: int = 512, quality: int = 55) -> bytes | None:
    """Encode an ndarray frame to a COMPACT JPEG: downscaled to ``max_width`` and
    quality-capped so multi-camera `look` responses stay small enough to traverse
    a tunnel (and encode fast enough to avoid origin timeouts)."""
    try:
        import cv2

        h, w = frame.shape[:2]
        if w > max_width:
            new_h = int(h * (max_width / w))
            frame = cv2.resize(frame, (max_width, new_h))
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return buf.tobytes() if ok else None
    except Exception:
        return None


@mcp.tool(annotations=_READ_ONLY)
def look(camera: str = "wrist", max_width: int = 512, quality: int = 55):
    """Capture the scene. ``camera`` selects 'wrist' (eye-in-hand, default), 'scene'
    (third-person), or 'both'. Defaulting to one compact image keeps responses small
    enough for a tunnel; pass camera='both' (and/or a larger max_width) when you
    need the overview too. In simulation, returns structured state only."""
    obs = _backend().look()
    state = _obs_to_dict(obs)
    frames = dict(obs.frames) if obs.frames else (
        {"front": obs.frame} if obs.frame is not None else {}
    )
    if camera != "both":
        selected = {k: v for k, v in frames.items() if k == camera}
        frames = selected or frames  # fall back if the requested name isn't present
    content: list = []
    for name, fr in frames.items():
        jpeg = _encode_jpeg(fr, max_width=max_width, quality=quality)
        if jpeg is not None:
            content.append(f"camera: {name}")
            content.append(Image(data=jpeg, format="jpeg"))
    if content:
        content.append(json.dumps(state))  # state as a trailing JSON text block
        return content
    return state


@mcp.tool(annotations=_ACTUATE)
def move_to(
    target: dict[str, float],
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    """Move toward a joint-space target. Keys are '<joint>.pos'. Clamped to safe limits.

    By default this waits for the observed pose to reach the target so agents do
    not plan the next step from a stale in-flight observation.
    """
    return _move_to(target, wait=wait, timeout=timeout, tolerance=tolerance)


@mcp.tool(annotations=_ACTUATE)
def move_relative(
    delta: dict[str, float],
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    """Nudge joints by RELATIVE degrees from the current pose. Keys are '<joint>.pos';
    only the given joints change, the rest hold. Clamped to safe limits.

    This is the composable primitive for *aligning* to a target whatever its
    position — small repeatable nudges (e.g. {"shoulder_pan.pos": -5}) you chain
    based on the camera, instead of a frozen absolute pose. Computed server-side
    (current+delta) so it costs one round-trip, not two."""
    backend = _backend()
    current = backend.get_observation().joints
    target = dict(current)
    for key, dv in delta.items():
        target[key] = current.get(key, 0.0) + float(dv)
    return _move_to(target, wait=wait, timeout=timeout, tolerance=tolerance)


@mcp.tool(annotations=_ACTUATE)
def set_gripper(
    position: float,
    wait: bool = True,
    timeout: float = 1.5,
    tolerance: float = 2.0,
) -> dict:
    """Command the gripper directly as a numeric ``gripper.pos`` target.

    This exposes the calibrated range instead of hiding it behind open/close
    presets, which is essential when calibration is narrow or inverted.
    """
    return _set_gripper(position, wait=wait, timeout=timeout, tolerance=tolerance)


@mcp.tool(annotations=_ACTUATE)
def grip(mode: str) -> dict:
    """Open or close the gripper. ``mode`` is 'open' or 'close'."""
    return _grip_mode(mode)


@mcp.tool(annotations=_READ_ONLY)
def wait_until_settled(
    timeout: float = 2.0,
    stable_tolerance: float = 0.75,
    stable_samples: int = 3,
) -> dict:
    """Poll observations until the pose stops changing, without commanding motion."""
    obs, motion = _wait_for_motion(
        None,
        timeout=timeout,
        stable_tolerance=stable_tolerance,
        stable_samples=stable_samples,
    )
    return _obs_with_motion(obs, motion)


@mcp.tool(annotations=_ACTUATE)
def home() -> dict:
    """Return the arm to its safe neutral pose."""
    from . import poses

    obs = _backend().home()
    target = clamp_action(poses.HOME)
    obs, motion = _wait_for_motion(target, timeout=2.0, tolerance=2.0)
    return _obs_with_motion(obs, motion, target)


@mcp.tool(annotations=_ACTUATE)
def run_sequence(
    steps: list,
    wait: bool = True,
    timeout_per_step: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    """Execute an ordered sequence of robot tool calls as one MCP round-trip.

    Supported steps: ``move_to``, ``move_relative``, ``set_gripper``, ``grip``,
    ``home``, and ``wait_until_settled``. Each motion step can wait for observed
    settling, making approach-close-lift routines less race-prone.
    """
    executed = []
    final: dict | None = None
    for raw in steps:
        call = sanitize_call(raw)
        tool = call["tool"]
        args = call.get("args", {})
        if tool == "move_to":
            final = _move_to(
                args["target"],
                wait=wait,
                timeout=float(args.get("timeout", timeout_per_step)),
                tolerance=float(args.get("tolerance", tolerance)),
            )
        elif tool == "move_relative":
            current = _backend().get_observation().joints
            target = dict(current)
            for key, dv in args["delta"].items():
                target[key] = current.get(key, 0.0) + float(dv)
            final = _move_to(
                target,
                wait=wait,
                timeout=float(args.get("timeout", timeout_per_step)),
                tolerance=float(args.get("tolerance", tolerance)),
            )
        elif tool == "set_gripper":
            final = _set_gripper(
                float(args["position"]),
                wait=wait,
                timeout=float(args.get("timeout", min(timeout_per_step, 1.5))),
                tolerance=float(args.get("tolerance", tolerance)),
            )
        elif tool == "grip":
            final = _grip_mode(
                args["mode"],
                wait=wait,
                timeout=float(args.get("timeout", min(timeout_per_step, 1.5))),
                tolerance=float(args.get("tolerance", tolerance)),
            )
        elif tool == "home":
            final = home()
        elif tool == "wait_until_settled":
            final = wait_until_settled(
                timeout=float(args.get("timeout", timeout_per_step)),
                stable_tolerance=float(args.get("stable_tolerance", 0.75)),
                stable_samples=int(args.get("stable_samples", 3)),
            )
        else:
            raise ValueError(f"unknown run_sequence tool: {tool!r}")
        executed.append({"tool": tool, "args": args, "motion": final.get("motion", {})})

    result = final or _obs_to_dict(_backend().get_observation())
    result["steps_executed"] = len(executed)
    result["trace"] = executed
    return result


@mcp.tool(annotations=_READ_ONLY)
def list_skills() -> list:
    """List saved robot skills (recorded, replayable tool-call sequences)."""
    from . import skills

    return skills.list_skills()


@mcp.tool(annotations=_WRITE)
def save_skill(name: str, steps: list, description: str = "", notes: str = "") -> dict:
    """Save a reusable skill from an ordered list of tool calls — each
    {"tool": "move_to"|"grip"|"home", "args": {...}}. Writes skills/<name>.json +
    a SKILL.md. Recording only — does NOT move the robot."""
    from . import skills

    saved = skills.save_skill(name, steps, description, notes)
    return {"saved": saved["name"], "steps": len(saved["steps"]), "path": f"skills/{name}.json"}


@mcp.tool(annotations=_ACTUATE)
def run_skill(name: str) -> dict:
    """Replay a saved skill: execute its recorded move_to/grip/home steps in order.
    Open-loop — only valid while the target is in the position it was taught for."""
    from . import skills

    skill = skills.load_skill(name)
    executed = 0
    final: dict | None = None
    for raw in skill.get("steps", []):
        call = sanitize_call(raw)
        tool = call["tool"]
        args = call.get("args", {})
        if tool == "move_to":
            final = _move_to(args["target"])
        elif tool == "move_relative":
            current = _backend().get_observation().joints
            target = dict(current)
            for key, dv in args["delta"].items():
                target[key] = current.get(key, 0.0) + float(dv)
            final = _move_to(target)
        elif tool == "set_gripper":
            final = _set_gripper(float(args["position"]))
        elif tool == "grip":
            final = _grip_mode(args["mode"])
        elif tool == "home":
            final = home()
        elif tool == "wait_until_settled":
            final = wait_until_settled(**args)
        else:
            raise ValueError(f"unknown tool in skill {name!r}: {tool!r}")
        executed += 1
    result = final or _obs_to_dict(_backend().get_observation())
    result["ran_skill"] = name
    result["steps_executed"] = executed
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Cygnus robot MCP server")
    parser.add_argument("--backend", default="sim", choices=["sim", "so101"])
    parser.add_argument("--port", help="serial port for the SO-101 (so101 backend)")
    parser.add_argument("--id", default="cygnus_follower", help="calibration id (so101 backend)")
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="OpenCV index for the wrist (eye-in-hand) camera; use -1 to run motion-only",
    )
    parser.add_argument(
        "--scene-camera-index",
        type=int,
        default=-1,
        help="optional OpenCV index for a distant/third-person 'scene' camera (-1 = none)",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="stdio (local subprocess) or http (network, for a remote tedi)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host for http/sse")
    parser.add_argument("--http-port", type=int, default=8000, help="bind port for http/sse")
    parser.add_argument(
        "--public-host",
        action="append",
        default=[],
        metavar="HOST",
        help="public hostname this server is reachable at behind a tunnel "
        "(e.g. cygnus.tedi.studio); repeatable. Added to the MCP DNS-rebinding "
        "allow-list so requests arriving with that Host header are accepted.",
    )
    args = parser.parse_args()

    global _robot
    if args.backend == "so101":
        if not args.port:
            parser.error("--port is required for the so101 backend (see `lerobot-find-port`)")
        _robot = build_backend(
            "so101",
            port=args.port,
            id=args.id,
            camera_index=args.camera_index,
            scene_camera_index=args.scene_camera_index,
        )
    else:
        _robot = build_backend("sim")
    _robot.connect()

    if args.transport == "stdio":
        mcp.run("stdio")
    else:
        # streamable-http / sse: bind a network listener a remote agent can reach.
        mcp.settings.host = args.host
        mcp.settings.port = args.http_port
        if args.public_host:
            # Behind a tunnel (e.g. cloudflared → cygnus.tedi.studio) the request
            # arrives with the public Host header, which DNS-rebinding protection
            # blocks by default. Allow the named hosts while keeping localhost.
            from mcp.server.transport_security import TransportSecuritySettings

            allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
            allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
            for h in args.public_host:
                allowed_hosts += [h, f"{h}:*"]
                allowed_origins += [f"https://{h}", f"http://{h}"]
            mcp.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=True,
                allowed_hosts=allowed_hosts,
                allowed_origins=allowed_origins,
            )
        mcp.run("streamable-http" if args.transport == "http" else "sse")


if __name__ == "__main__":
    main()
