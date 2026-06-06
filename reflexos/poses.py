"""Named-pose vocabulary — the shared "kinematics table".

Both the simulator (which resolves whether the gripper is *at* a zone) and the
reasoner (which plans *toward* a zone) speak in terms of these named poses, the
way a real deployment would share a calibration table. Values are illustrative
joint angles in degrees, not a true SO-101 IK solution.
"""

from __future__ import annotations

from .types import JOINTS, Plan

OPEN_GRIP = 60.0
CLOSED_GRIP = 15.0
APPROACH_TOL = 10.0  # degrees; how close counts as "at" a pose


def pose(
    pan: float,
    lift: float,
    elbow: float,
    wrist_flex: float = 0.0,
    wrist_roll: float = 0.0,
    grip: float = OPEN_GRIP,
) -> dict[str, float]:
    """Build a ``"<joint>.pos"`` dict from joint angles."""
    values = [pan, lift, elbow, wrist_flex, wrist_roll, grip]
    return {f"{name}.pos": float(v) for name, v in zip(JOINTS, values)}


# The single canonical home: the live-taught rest pose, folded back over the
# harness/base with the wrist camera pointed up and clear of the table. It is
# ARM-ONLY (no gripper) on purpose — homing must never drop a carried object;
# open/close the claw explicitly with `set_gripper` when you actually mean to.
# The `home` tool and the `home` skill both target this exact pose; keep them in
# sync (the skill audit enforces it).
HOME = {
    "shoulder_pan.pos": 3.1,
    "shoulder_lift.pos": -99.5,
    "elbow_flex.pos": 96.7,
    "wrist_flex.pos": 16.2,
    "wrist_roll.pos": -96.8,
}

# Cube pick locations. The arm's *habit* is trained for zone "A"; "B"/"C" are
# the novel placements that constitute black swans for a blind habit.
ZONE_POSE: dict[str, dict[str, float]] = {
    "A": pose(-30, -45, 55),
    "B": pose(0, -50, 60),
    "C": pose(30, -45, 55),
}

# Where the cube is dropped. Gripper stays closed while carrying.
BIN_POSE = pose(75, -30, 40, grip=CLOSED_GRIP)

_NEAR_KEYS = ("shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos")


def near(joints: dict[str, float], target: dict[str, float], tol: float = APPROACH_TOL) -> bool:
    """True if ``joints`` is within ``tol`` of ``target`` on the major axes."""
    return all(abs(joints.get(k, 1e9) - target[k]) <= tol for k in _NEAR_KEYS)


def grasp_and_place_plan(zone: str) -> Plan:
    """The canonical pick-and-place plan for a cube in ``zone``.

    Used both as the fixed System-1 *habit* (zone "A") and as the body of a
    System-2 *recovery* once the reasoner perceives the cube's true zone.
    """
    return [
        {"tool": "move_to", "args": {"target": ZONE_POSE[zone]}},
        {"tool": "grip", "args": {"mode": "close"}},
        {"tool": "move_to", "args": {"target": BIN_POSE}},
        {"tool": "grip", "args": {"mode": "open"}},
    ]
