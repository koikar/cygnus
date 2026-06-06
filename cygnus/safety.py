"""Immutable safety guardrails.

These constraints live below the learning loop: the cognitive layer can add new
reflexes, but it can never relax a limit defined here. This is the
anti-"misevolution" boundary — antifragility must not come at the cost of safety.
"""

from __future__ import annotations

from .types import ToolCall

# Conservative per-joint software limits in degrees (gripper in 0..100 %).
JOINT_LIMITS: dict[str, tuple[float, float]] = {
    "shoulder_pan.pos": (-110.0, 110.0),
    "shoulder_lift.pos": (-100.0, 100.0),
    "elbow_flex.pos": (-100.0, 100.0),
    "wrist_flex.pos": (-100.0, 100.0),
    "wrist_roll.pos": (-180.0, 180.0),
    "gripper.pos": (0.0, 100.0),
}


def clamp_action(action: dict[str, float]) -> dict[str, float]:
    """Clamp every joint target into its safe range. Unknown keys pass through."""
    safe: dict[str, float] = {}
    for key, value in action.items():
        if key in JOINT_LIMITS:
            lo, hi = JOINT_LIMITS[key]
            safe[key] = max(lo, min(hi, float(value)))
        # Unknown keys are dropped, never forwarded — keeps a typo'd or injected
        # joint name (a remotely-reachable actuation surface) off the motor bus.
    return safe


def is_within_limits(action: dict[str, float]) -> bool:
    """True if every limited joint target is already inside its range."""
    for key, value in action.items():
        if key in JOINT_LIMITS:
            lo, hi = JOINT_LIMITS[key]
            if not (lo <= float(value) <= hi):
                return False
    return True


def sanitize_call(call: ToolCall) -> ToolCall:
    """Clamp any ``move_to`` target inside a tool call before it reaches a backend."""
    if call.get("tool") == "move_to":
        target = call.get("args", {}).get("target", {})
        call = {"tool": "move_to", "args": {"target": clamp_action(target)}}
    return call


# --- Cartesian workspace supervisor ---------------------------------------
# A conservative base-frame box (metres) the end-effector must stay inside. These
# are derived from the measured FK reach envelope and MUST be tuned to the real
# table; they are a backstop so a bad IK target / vision projection can't drive
# the arm out of bounds. Override via env for a different rig.
import os as _os  # noqa: E402

WORKSPACE_BOUNDS: dict[str, tuple[float, float]] = {
    "x": (float(_os.getenv("CYGNUS_WS_XMIN", "0.08")), float(_os.getenv("CYGNUS_WS_XMAX", "0.46"))),
    "y": (float(_os.getenv("CYGNUS_WS_YMIN", "-0.28")), float(_os.getenv("CYGNUS_WS_YMAX", "0.28"))),
    "z": (float(_os.getenv("CYGNUS_WS_ZMIN", "-0.10")), float(_os.getenv("CYGNUS_WS_ZMAX", "0.38"))),
}
# Largest Cartesian step (metres) any single EE move may command.
MAX_STEP_M: float = float(_os.getenv("CYGNUS_MAX_STEP_M", "0.05"))


def within_workspace(x: float, y: float, z: float) -> bool:
    """True if a base-frame point is inside the safe Cartesian box."""
    return all(
        lo <= v <= hi
        for v, (lo, hi) in zip((x, y, z), (WORKSPACE_BOUNDS["x"], WORKSPACE_BOUNDS["y"], WORKSPACE_BOUNDS["z"]))
    )


def check_ee_target(x: float, y: float, z: float) -> None:
    """Raise ValueError if an EE target is outside the workspace box.

    The Cartesian counterpart to clamp_action: a backstop the move_ee_* tools call
    before solving IK, so a bad vision projection can't send the arm out of bounds.
    """
    if not within_workspace(x, y, z):
        raise ValueError(
            f"EE target ({x:.3f}, {y:.3f}, {z:.3f}) m is outside the safe workspace "
            f"{WORKSPACE_BOUNDS}"
        )
