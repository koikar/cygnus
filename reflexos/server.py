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
    python -m reflexos.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --camera-index 1 --transport stdio
    # reachable by a remote tedi:
    python -m reflexos.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --camera-index 1 --transport http --host 0.0.0.0 --http-port 8000
"""

from __future__ import annotations

import argparse
import json
import time

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ToolAnnotations

from .motion_lock import motion_lock
from .robot import build_backend
from .robot.base import RobotBackend
from .safety import (
    JOINT_LIMITS,
    MAX_STEP_M,
    WORKSPACE_BOUNDS,
    check_ee_target,
    clamp_action,
    sanitize_call,
)
from .types import Observation

mcp = FastMCP("reflexos-robot")

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
        raise RuntimeError("robot backend not initialized; run via `python -m reflexos.server`")
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


def _get_ee_pose_dict(joints: dict[str, float] | None = None) -> dict:
    from .kinematics import so101_kinematics

    joints = joints or _backend().get_observation().joints
    return so101_kinematics().pose(joints).as_dict()


def _maybe_get_ee_pose_dict(joints: dict[str, float]) -> dict:
    try:
        return {"available": True, "pose": _get_ee_pose_dict(joints)}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _get_joint_effects_dict(
    joints: dict[str, float] | None = None,
    *,
    step_degrees: float = 1.0,
) -> dict:
    from .kinematics import so101_kinematics

    joints = joints or _backend().get_observation().joints
    return so101_kinematics().joint_effects(joints, step_deg=step_degrees)


def _maybe_get_joint_effects_dict(joints: dict[str, float], *, step_degrees: float = 1.0) -> dict:
    try:
        return {
            "available": True,
            "proprioception": _get_joint_effects_dict(joints, step_degrees=step_degrees),
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _load_table_calibration(camera: str):
    from .calibration import TableCalibration

    return TableCalibration.load(camera)


def _project_pixel_to_table_dict(u: float, v: float, *, camera: str = "scene") -> dict:
    cal = _load_table_calibration(camera)
    target = cal.pixel_to_table(u, v)
    workspace_ok = True
    workspace_error = None
    try:
        check_ee_target(target["x"], target["y"], target["z"])
    except ValueError as exc:
        workspace_ok = False
        workspace_error = str(exc)
    return {
        "camera": cal.camera,
        "pixel": {"x": float(u), "y": float(v)},
        "table_target": target,
        "workspace_ok": workspace_ok,
        "workspace_error": workspace_error,
    }


def _move_ee_to(
    *,
    x: float,
    y: float,
    z: float,
    wx: float | None = None,
    wy: float | None = None,
    wz: float | None = None,
    gripper: float | None = None,
    orientation_weight: float = 0.01,
    max_step_m: float = 0.04,
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    import math

    from .kinematics import EEPose, so101_kinematics

    max_step_m = float(max_step_m)
    if max_step_m <= 0:
        raise ValueError("max_step_m must be positive")
    max_step_m = min(max_step_m, MAX_STEP_M)

    obs = _backend().get_observation()
    kin = so101_kinematics()
    current_pose = kin.pose(obs.joints)
    requested_pose = EEPose(
        x=float(x),
        y=float(y),
        z=float(z),
        wx=current_pose.wx if wx is None else float(wx),
        wy=current_pose.wy if wy is None else float(wy),
        wz=current_pose.wz if wz is None else float(wz),
        matrix=current_pose.matrix,
    )
    check_ee_target(requested_pose.x, requested_pose.y, requested_pose.z)
    dx = requested_pose.x - current_pose.x
    dy = requested_pose.y - current_pose.y
    dz = requested_pose.z - current_pose.z
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    target_pose = requested_pose
    clipped = False
    if distance > max_step_m and distance > 0:
        scale = max_step_m / distance
        target_pose = EEPose(
            x=current_pose.x + dx * scale,
            y=current_pose.y + dy * scale,
            z=current_pose.z + dz * scale,
            wx=requested_pose.wx,
            wy=requested_pose.wy,
            wz=requested_pose.wz,
            matrix=current_pose.matrix,
        )
        clipped = True
    check_ee_target(target_pose.x, target_pose.y, target_pose.z)

    target = kin.solve(
        obs.joints,
        target_pose,
        gripper=gripper,
        orientation_weight=orientation_weight,
    )
    result = _move_to(target, wait=wait, timeout=timeout, tolerance=tolerance)
    result["ee"] = {
        "current": current_pose.as_dict(),
        "requested": requested_pose.as_dict(),
        "target": target_pose.as_dict(),
        "clipped_to_max_step": clipped,
        "requested_distance_m": distance,
        "max_step_m": max_step_m,
        "orientation_weight": orientation_weight,
    }
    return result


def _move_ee_by(
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
    dwx: float = 0.0,
    dwy: float = 0.0,
    dwz: float = 0.0,
    gripper: float | None = None,
    orientation_weight: float = 0.01,
    max_step_m: float = 0.04,
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    from .kinematics import so101_kinematics

    max_step_m = float(max_step_m)
    if max_step_m <= 0:
        raise ValueError("max_step_m must be positive")
    max_step_m = min(max_step_m, MAX_STEP_M)

    obs = _backend().get_observation()
    kin = so101_kinematics()
    current_pose = kin.pose(obs.joints)
    target_pose = kin.offset_pose(
        current_pose,
        dx=dx,
        dy=dy,
        dz=dz,
        dwx=dwx,
        dwy=dwy,
        dwz=dwz,
        max_step_m=max_step_m,
    )
    return _move_ee_to(
        x=target_pose.x,
        y=target_pose.y,
        z=target_pose.z,
        wx=target_pose.wx,
        wy=target_pose.wy,
        wz=target_pose.wz,
        gripper=gripper,
        orientation_weight=orientation_weight,
        max_step_m=max_step_m,
        wait=wait,
        timeout=timeout,
        tolerance=tolerance,
    )


@mcp.tool(annotations=_READ_ONLY)
def get_capabilities() -> dict:
    """Return the robot MCP contract and safety envelope."""
    return {
        "name": "reflexos-robot",
        "backend": _backend().name,
        "tools": {
            "look": "Capture the camera image plus current robot state.",
            "detect_colored_blocks": "Return simple HSV color blob candidates from a camera.",
            "fit_table_calibration": "Fit/save pixel-to-table calibration from point correspondences.",
            "get_table_calibration": "Load the saved pixel-to-table calibration for a camera.",
            "project_pixel_to_table": "Project a pixel through the saved calibration to a safe table target.",
            "get_state": "Return joint positions and structured scene state.",
            "get_robot_model": "Return joints, limits, presets, cameras, and current state.",
            "get_ee_pose": "Return end-effector pose from FK.",
            "get_joint_effects": "Return live per-joint FK effects: what +1 degree does to the claw.",
            "move_to": "Move toward safe joint-space targets; targets are clamped.",
            "move_relative": "Nudge joints relative to the current pose.",
            "move_ee_to": "Move the gripper toward a Cartesian pose via IK.",
            "move_ee_by": "Translate/rotate the gripper by a small Cartesian delta via IK.",
            "set_gripper": "Command a numeric gripper position.",
            "grip": "Open or close the gripper.",
            "verify_grasp": "Twist the wrist to definitively check held vs empty (reliable gate).",
            "wait_until_settled": "Poll until the observed pose stops changing.",
            "run_sequence": "Execute an atomic multi-step tool sequence.",
            "home": "Return to the harness-rest pose with the wrist camera facing upward.",
            "audit_skills": "Validate saved skills against the learned home/reach/grab body schema.",
        },
        "hardware_channels": {
            "motion": "SO-101 follower / Feetech serial bus over USB",
            "vision": "OpenCV/UVC camera over USB",
        },
        "safety": {
            "move_to_clamped": True,
            "workspace_bounds_m": WORKSPACE_BOUNDS,
            "max_default_ee_step_m": 0.04,
            "max_allowed_ee_step_m": MAX_STEP_M,
            "motion_lock": "one actuation command or sequence runs at a time",
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
        "end_effector": {
            "pose_tool": "get_ee_pose",
            "move_tools": ["move_ee_by", "move_ee_to"],
            "frame": "base_link",
            "target_frame": "gripper_frame_link",
            "units": {"position": "meters", "rotation": "radians_rotvec"},
            "default_max_step_m": 0.04,
            "max_allowed_step_m": MAX_STEP_M,
            "workspace_bounds_m": WORKSPACE_BOUNDS,
            "current": _maybe_get_ee_pose_dict(state["joints"]),
        },
        "proprioception": {
            "tool": "get_joint_effects",
            "meaning": "pose-dependent finite-difference FK map from joint degrees to claw movement",
            "default_step_degrees": 1.0,
            "current": _maybe_get_joint_effects_dict(state["joints"], step_degrees=1.0),
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


@mcp.tool(annotations=_READ_ONLY)
def detect_colored_blocks(
    camera: str = "scene",
    min_area: float = 120.0,
    max_area: float = 3000.0,
    max_results: int = 12,
    roi: dict | None = None,
    include_table_targets: bool = True,
) -> dict:
    """Return simple color-blob target candidates from a camera frame.

    This is a lightweight tabletop helper, not a full detector. Use it to choose
    candidate pixels for purple/cyan/orange/blue blocks. Once table calibration
    exists, detections include base-frame table targets agents can feed to
    `move_ee_to`.
    """
    from .vision import detect_colored_blocks as detect

    obs = _backend().look()
    frames = dict(obs.frames) if obs.frames else (
        {"front": obs.frame} if obs.frame is not None else {}
    )
    if camera in frames:
        selected_camera = camera
        frame = frames[camera]
    elif frames:
        selected_camera, frame = next(iter(frames.items()))
    else:
        selected_camera, frame = camera, None
    if frame is None:
        return {"camera": camera, "detections": [], "state": _obs_to_dict(obs)}
    detections = detect(
        frame,
        min_area=min_area,
        max_area=max_area,
        max_results=max_results,
        roi=roi,
    )
    calibration = {"available": False}
    if include_table_targets:
        try:
            calibration = {"available": True, "camera": selected_camera}
            for detection in detections:
                center = detection.get("center", {})
                projection = _project_pixel_to_table_dict(
                    float(center["x"]),
                    float(center["y"]),
                    camera=selected_camera,
                )
                detection["table_target"] = projection["table_target"]
                detection["workspace_ok"] = projection["workspace_ok"]
                if projection["workspace_error"]:
                    detection["workspace_error"] = projection["workspace_error"]
        except FileNotFoundError as exc:
            calibration = {"available": False, "error": str(exc)}
    return {
        "camera": selected_camera,
        "detections": detections,
        "calibration": calibration,
        "roi": roi,
        "state": _obs_to_dict(obs),
    }


@mcp.tool(annotations=_WRITE)
def fit_table_calibration(
    correspondences: list,
    table_z: float,
    camera: str = "scene",
) -> dict:
    """Fit and save pixel→table calibration for one camera.

    `correspondences` is a list of {"pixel": [u, v], "table": [x, y]} records.
    The saved homography lets agents turn visual detections into base-frame
    `move_ee_to` targets on the table plane.
    """
    from .calibration import fit

    cal = fit(correspondences, table_z=table_z, camera=camera)
    path = cal.save()
    return {
        "camera": camera,
        "samples": len(correspondences),
        "table_z": table_z,
        "max_residual_m": getattr(cal, "max_residual_m", None),
        "path": str(path),
        "calibration": cal.to_dict(),
    }


@mcp.tool(annotations=_READ_ONLY)
def get_table_calibration(camera: str = "scene") -> dict:
    """Load the saved pixel→table calibration for a camera."""
    cal = _load_table_calibration(camera)
    return {"available": True, "calibration": cal.to_dict()}


@mcp.tool(annotations=_READ_ONLY)
def project_pixel_to_table(u: float, v: float, camera: str = "scene") -> dict:
    """Project one image pixel to a base-frame table target with workspace status."""
    return _project_pixel_to_table_dict(u, v, camera=camera)


@mcp.tool(annotations=_READ_ONLY)
def get_ee_pose() -> dict:
    """Return the current end-effector pose from FK.

    Position is meters in the URDF base frame; orientation is a rotation vector
    in radians. This is the body schema used by Cartesian movement tools.
    """
    obs = _backend().get_observation()
    result = _obs_to_dict(obs)
    result["ee_pose"] = _get_ee_pose_dict(obs.joints)
    return result


@mcp.tool(annotations=_READ_ONLY)
def get_joint_effects(step_degrees: float = 1.0) -> dict:
    """Return what a positive joint delta means for the claw at the current pose.

    This is read-only proprioception. It uses FK finite differences, not motor
    motion: for each joint, it reports how ``+step_degrees`` changes the
    end-effector position in meters/millimeters and orientation in radians.
    Because the mapping is pose-dependent, call this before planning joint-space
    nudges.
    """
    obs = _backend().get_observation()
    result = _obs_to_dict(obs)
    result["joint_effects"] = _get_joint_effects_dict(
        obs.joints,
        step_degrees=step_degrees,
    )
    return result


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
    with motion_lock(owner="move_to"):
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
    with motion_lock(owner="move_relative"):
        backend = _backend()
        current = backend.get_observation().joints
        target = dict(current)
        for key, dv in delta.items():
            target[key] = current.get(key, 0.0) + float(dv)
        return _move_to(target, wait=wait, timeout=timeout, tolerance=tolerance)


@mcp.tool(annotations=_ACTUATE)
def move_ee_to(
    x: float,
    y: float,
    z: float,
    wx: float | None = None,
    wy: float | None = None,
    wz: float | None = None,
    gripper: float | None = None,
    orientation_weight: float = 0.01,
    max_step_m: float = 0.04,
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    """Move the gripper toward a Cartesian pose using FK/IK.

    Position is meters in the URDF base frame. Orientation defaults to the
    current gripper orientation; pass ``wx/wy/wz`` to request a rotvec target.
    Large translations are clipped to ``max_step_m`` so agents can safely repeat
    the call instead of issuing a single large IK jump.

    CAVEAT (live SO-101): Cartesian IK is **unreliable in the near-vertical,
    wrist-down grasp configuration** used for tabletop picks — placo under-converges
    and small deltas can return as no-ops (target == current). For tabletop work,
    prefer joint-space ``move_to``/``move_relative`` and verify with ``get_state``.
    """
    with motion_lock(owner="move_ee_to"):
        return _move_ee_to(
            x=x,
            y=y,
            z=z,
            wx=wx,
            wy=wy,
            wz=wz,
            gripper=gripper,
            orientation_weight=orientation_weight,
            max_step_m=max_step_m,
            wait=wait,
            timeout=timeout,
            tolerance=tolerance,
        )


@mcp.tool(annotations=_ACTUATE)
def move_ee_by(
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
    dwx: float = 0.0,
    dwy: float = 0.0,
    dwz: float = 0.0,
    gripper: float | None = None,
    orientation_weight: float = 0.01,
    max_step_m: float = 0.04,
    wait: bool = True,
    timeout: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    """Translate/rotate the gripper by a small Cartesian delta using FK/IK.

    Position deltas are meters in the URDF base frame; rotation deltas are
    radians added to the current rotation vector.

    CAVEAT (live SO-101): unreliable in the near-vertical wrist-down grasp config —
    placo IK under-converges there, so deltas may return as no-ops (the EE does not
    actually move). It is **not** a dependable approach/descend/lift primitive for
    tabletop picks; use joint-space ``move_relative`` and confirm with ``get_state``.
    Cartesian control is fine in more open, mid-workspace poses.
    """
    with motion_lock(owner="move_ee_by"):
        return _move_ee_by(
            dx=dx,
            dy=dy,
            dz=dz,
            dwx=dwx,
            dwy=dwy,
            dwz=dwz,
            gripper=gripper,
            orientation_weight=orientation_weight,
            max_step_m=max_step_m,
            wait=wait,
            timeout=timeout,
            tolerance=tolerance,
        )


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
    with motion_lock(owner="set_gripper"):
        return _set_gripper(position, wait=wait, timeout=timeout, tolerance=tolerance)


@mcp.tool(annotations=_ACTUATE)
def grip(mode: str) -> dict:
    """Open or close the gripper. ``mode`` is 'open' or 'close'."""
    with motion_lock(owner="grip"):
        return _grip_mode(mode)


def _wrist_cube_blob() -> dict | None:
    """Largest *compact* color blob in the wrist frame (the held object), or None.

    Rejects elongated blobs (table tape / grid lines) by aspect ratio so the
    object — not the workspace markings — is tracked across the twist.
    """
    from .vision import detect_colored_blocks as detect

    obs = _backend().look()
    frames = dict(obs.frames) if obs.frames else (
        {"wrist": obs.frame} if obs.frame is not None else {}
    )
    frame = frames.get("wrist")
    if frame is None and frames:
        frame = next(iter(frames.values()))
    if frame is None:
        return None
    best = None
    for d in detect(frame, max_results=15):
        bb = d.get("bbox", {})
        w, h = bb.get("width", 1), bb.get("height", 1)
        if max(w, h) / max(1, min(w, h)) > 3.0:  # elongated -> tape/grid line, not the cube
            continue
        if best is None or d["area_px"] > best["area_px"]:
            best = d
    return best


@mcp.tool(annotations=_ACTUATE)
def verify_grasp(twist_deg: float = 35.0, shift_threshold_px: float = 60.0) -> dict:
    """Definitively check whether the gripper is HOLDING an object, via a wrist twist.

    Neither ``gripper.pos`` nor a top-down wrist ``look`` distinguishes held from
    empty for a small object: empty-close ~= held-close, and an object still on the
    table directly below the lifted jaws still looks "between" them (the wrist cam
    points down and moves with the claw). The trustworthy gate is a twist: rotate
    ``wrist_roll`` by ``twist_deg`` and back, watching the largest wrist-cam blob.
    A **held** object rotates *with* the jaws and barely shifts in-frame; a
    **missed** object stays on the table while the camera sweeps, so its blob
    shifts far (or vanishes).

    Run right after close + lift. Uses the camera, so call it deliberately — it is
    slower than state-only moves. Returns a verdict ("held" / "empty" / "uncertain")
    with the measured pixel shift so the caller can apply its own judgement.
    """
    from . import poses

    with motion_lock(owner="verify_grasp"):
        state = _backend().get_observation().joints
        grip_pos = state.get("gripper.pos", 999.0)
        if grip_pos > poses.OPEN_GRIP * 0.6:  # jaws clearly open -> nothing to hold
            return {"verdict": "empty", "reason": "gripper_open", "gripper_pos": round(grip_pos, 1)}
        roll0 = state.get("wrist_roll.pos", 0.0)
        before = _wrist_cube_blob()
        _move_to({"wrist_roll.pos": roll0 + twist_deg}, timeout=3.0, tolerance=1.5)
        after = _wrist_cube_blob()
        _move_to({"wrist_roll.pos": roll0}, timeout=3.0, tolerance=1.5)  # untwist
        if before is None or after is None:
            return {
                "verdict": "uncertain",
                "reason": "no_blob_detected",
                "before": before,
                "after": after,
                "gripper_pos": round(grip_pos, 1),
            }
        dx = after["center"]["x"] - before["center"]["x"]
        dy = after["center"]["y"] - before["center"]["y"]
        shift = (dx * dx + dy * dy) ** 0.5
        return {
            "verdict": "held" if shift <= shift_threshold_px else "empty",
            "shift_px": round(shift, 1),
            "threshold_px": shift_threshold_px,
            "twist_deg": twist_deg,
            "before_center": before["center"],
            "after_center": after["center"],
            "gripper_pos": round(grip_pos, 1),
        }


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
    """Return the arm to the harness-rest pose with wrist camera facing upward."""
    from . import poses

    with motion_lock(owner="home"):
        obs = _backend().home()
        target = clamp_action(poses.HOME)
        obs, motion = _wait_for_motion(target, timeout=2.0, tolerance=2.0)
        return _obs_with_motion(obs, motion, target)


@mcp.tool(annotations=_ACTUATE)
def relax(enabled: bool = False) -> dict:
    """Enable or disable motor holding torque (for kinesthetic hand-teaching).

    relax(enabled=False) makes the arm LIMP so it can be posed by hand; then
    capture the pose with get_state and save_skill. relax(enabled=True) re-locks
    it to hold position.

    WARNING: with torque off the arm SAGS/DROPS under gravity — support it and
    relax from a low pose. Re-enable torque before issuing any motion command.
    """
    backend = _backend()
    set_torque = getattr(backend, "set_torque", None)
    if set_torque is None:
        raise RuntimeError("torque control is only available on the real SO-101 backend")
    with motion_lock(owner="relax"):
        set_torque(enabled)
    result = _obs_to_dict(backend.get_observation())
    result["torque_enabled"] = enabled
    return result


@mcp.tool(annotations=_ACTUATE)
def set_speed(acceleration: int = 30, velocity: int | None = None) -> dict:
    """Set how smooth/slow the arm moves (applies to all subsequent moves).

    Lower ``acceleration`` (0-254) = gentler, less abrupt starts/stops; LeRobot's
    default is 254 (snappiest). ``velocity`` caps top speed (Goal_Velocity; 0/None
    leaves the servo default). Good demo values: acceleration ~20-40.
    """
    backend = _backend()
    set_profile = getattr(backend, "set_motion_profile", None)
    if set_profile is None:
        raise RuntimeError("motion-profile control is only available on the real SO-101 backend")
    acc = max(0, min(254, int(acceleration)))
    with motion_lock(owner="set_speed"):
        set_profile(acceleration=acc, velocity=velocity)
    return {"acceleration": acc, "velocity": velocity, "note": "lower acceleration = smoother"}


@mcp.tool(annotations=_ACTUATE)
def run_sequence(
    steps: list,
    wait: bool = True,
    timeout_per_step: float = 2.0,
    tolerance: float = 2.0,
) -> dict:
    """Execute an ordered sequence of robot tool calls as one MCP round-trip.

    Supported steps: ``move_to``, ``move_relative``, ``move_ee_to``,
    ``move_ee_by``, ``set_gripper``, ``grip``, ``home``, ``wait_until_settled``,
    ``verify_grasp`` (wrist-twist held/empty check), and ``skill`` (inline another
    saved skill by ``{"tool": "skill", "args": {"name": ...}}``). Each motion step
    can wait for observed settling, making approach-close-lift routines less race-prone.
    """
    with motion_lock(owner="run_sequence"):
        return _run_sequence_unlocked(
            steps,
            wait=wait,
            timeout_per_step=timeout_per_step,
            tolerance=tolerance,
        )


def _run_sequence_unlocked(
    steps: list,
    *,
    wait: bool = True,
    timeout_per_step: float = 2.0,
    tolerance: float = 2.0,
    _depth: int = 0,
) -> dict:
    executed = []
    final: dict | None = None
    for raw in steps:
        call = sanitize_call(raw)
        tool = call["tool"]
        args = call.get("args", {})
        if tool == "skill":
            # Composed reference: inline another saved skill's steps. Lets pick/place
            # skills reference paper_pos_N so re-teaching a position updates them all.
            if _depth >= 5:
                raise ValueError("skill composition nested too deep (cycle?)")
            from . import skills as _skills

            sub = _skills.load_skill(args["name"])
            final = _run_sequence_unlocked(
                sub.get("steps", []),
                wait=wait,
                timeout_per_step=timeout_per_step,
                tolerance=tolerance,
                _depth=_depth + 1,
            )
        elif tool == "verify_grasp":
            final = verify_grasp(
                twist_deg=float(args.get("twist_deg", 35.0)),
                shift_threshold_px=float(args.get("shift_threshold_px", 60.0)),
            )
        elif tool == "move_to":
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
        elif tool == "move_ee_to":
            final = _move_ee_to(
                x=float(args["x"]),
                y=float(args["y"]),
                z=float(args["z"]),
                wx=args.get("wx"),
                wy=args.get("wy"),
                wz=args.get("wz"),
                gripper=args.get("gripper"),
                orientation_weight=float(args.get("orientation_weight", 0.01)),
                max_step_m=float(args.get("max_step_m", 0.04)),
                wait=wait,
                timeout=float(args.get("timeout", timeout_per_step)),
                tolerance=float(args.get("tolerance", tolerance)),
            )
        elif tool == "move_ee_by":
            final = _move_ee_by(
                dx=float(args.get("dx", 0.0)),
                dy=float(args.get("dy", 0.0)),
                dz=float(args.get("dz", 0.0)),
                dwx=float(args.get("dwx", 0.0)),
                dwy=float(args.get("dwy", 0.0)),
                dwz=float(args.get("dwz", 0.0)),
                gripper=args.get("gripper"),
                orientation_weight=float(args.get("orientation_weight", 0.01)),
                max_step_m=float(args.get("max_step_m", 0.04)),
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


@mcp.tool(annotations=_READ_ONLY)
def audit_skills() -> dict:
    """Validate saved skills against the current learned body schema.

    This catches stale/open-loop lessons such as roll-based "grabbing" and
    confirms the required home → reach → flex-down grab → home skills exist.
    """
    from .skill_audit import audit_skills as audit

    return audit()


@mcp.tool(annotations=_WRITE)
def save_skill(
    name: str, steps: list, description: str = "", notes: str = "", kind: str = ""
) -> dict:
    """Save a reusable skill from an ordered list of tool calls — each
    {"tool": "move_to"|"move_ee_by"|"grip"|"skill"|..., "args": {...}}. ``kind`` is
    an optional intent tag (position/pick/place/primitive/home/demo) for filtering.
    Writes skills/<name>.json + a SKILL.md. Recording only — does NOT move the robot."""
    from . import skills

    saved = skills.save_skill(name, steps, description, notes, kind)
    return {"saved": saved["name"], "kind": saved.get("kind", ""), "steps": len(saved["steps"]), "path": f"skills/{name}.json"}


@mcp.tool(annotations=_ACTUATE)
def run_skill(name: str) -> dict:
    """Replay a saved skill: execute its recorded move_to/grip/home steps in order.
    Open-loop — only valid while the target is in the position it was taught for."""
    from . import skills

    with motion_lock(owner=f"run_skill:{name}"):
        skill = skills.load_skill(name)
        result = _run_sequence_unlocked(skill.get("steps", []))
        result["ran_skill"] = name
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="ReflexOS robot MCP server")
    parser.add_argument("--backend", default="sim", choices=["sim", "so101"])
    parser.add_argument("--port", help="serial port for the SO-101 (so101 backend)")
    parser.add_argument("--id", default="reflexos_follower", help="calibration id (so101 backend)")
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
        "(e.g. reflexos.tedi.studio); repeatable. Added to the MCP DNS-rebinding "
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
            # Behind a tunnel (e.g. cloudflared → reflexos.tedi.studio) the request
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
