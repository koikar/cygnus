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
        else:
            safe[key] = value
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
