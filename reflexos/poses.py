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


# The physical resting pose: folded backward onto the harness/base area, with the
# wrist camera pointed upward toward the ceiling. Validated on the live SO-101.
# (An alternate live-taught rest pose is saved as the `home_v2` skill; changing
# this canonical HOME requires re-validating the home→reach→grab→home demo.)
HOME = pose(0, -45, 95, -70, grip=60)

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
