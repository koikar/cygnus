"""SO-101 end-effector kinematics.

This wraps LeRobot's placo-backed ``RobotKinematics`` behind a small local API
that speaks Cygnus joint dictionaries. Imports stay lazy so the simulator and
tests do not require the hardware stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .safety import JOINT_LIMITS, clamp_action
from .types import JOINTS

ARM_JOINTS = [name for name in JOINTS if name != "gripper"]
URDF_PATH = Path(__file__).parent / "assets" / "so101" / "so101_kinematics.urdf"
POSE_KEYS = ("x", "y", "z", "wx", "wy", "wz")


@dataclass(frozen=True)
class EEPose:
    x: float
    y: float
    z: float
    wx: float
    wy: float
    wz: float
    matrix: list[list[float]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "wx": self.wx,
            "wy": self.wy,
            "wz": self.wz,
            "matrix": self.matrix,
            "units": {"position": "meters", "rotation": "radians_rotvec"},
            "frame": "base_link",
            "target_frame": "gripper_frame_link",
        }


class SO101Kinematics:
    def __init__(self, urdf_path: Path = URDF_PATH) -> None:
        self.urdf_path = urdf_path
        self._kinematics = None

    @property
    def kinematics(self):
        if self._kinematics is None:
            from lerobot.model.kinematics import RobotKinematics

            self._kinematics = RobotKinematics(
                str(self.urdf_path),
                target_frame_name="gripper_frame_link",
                joint_names=ARM_JOINTS,
            )
        return self._kinematics

    def pose(self, joints: dict[str, float]) -> EEPose:
        import numpy as np
        from lerobot.utils.rotation import Rotation

        q = np.array([float(joints[f"{name}.pos"]) for name in ARM_JOINTS], dtype=float)
        matrix = self.kinematics.forward_kinematics(q)
        pos = matrix[:3, 3]
        rotvec = Rotation.from_matrix(matrix[:3, :3]).as_rotvec()
        return EEPose(
            x=float(pos[0]),
            y=float(pos[1]),
            z=float(pos[2]),
            wx=float(rotvec[0]),
            wy=float(rotvec[1]),
            wz=float(rotvec[2]),
            matrix=matrix.tolist(),
        )

    def joint_effects(self, joints: dict[str, float], *, step_deg: float = 1.0) -> dict[str, Any]:
        """Finite-difference body schema: what +step degrees does at this pose."""
        step_deg = float(step_deg)
        if step_deg == 0:
            raise ValueError("step_deg must be non-zero")

        base_pose = self.pose(joints)
        base = base_pose.as_dict()
        effects: dict[str, Any] = {}
        for name in JOINTS:
            key = f"{name}.pos"
            current = float(joints[key])
            target = clamp_action({key: current + step_deg})[key]
            actual_step = target - current
            if name == "gripper":
                effects[key] = {
                    "joint": name,
                    "current_deg": current,
                    "sample_step_deg": actual_step,
                    "semantic": "jaw open/close only; no end-effector FK translation",
                    "position_delta_m": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "position_delta_mm": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "rotation_delta_rad": {"wx": 0.0, "wy": 0.0, "wz": 0.0},
                    "per_degree_mm": {"x": 0.0, "y": 0.0, "z": 0.0},
                }
                continue

            moved_joints = dict(joints)
            moved_joints[key] = target
            moved = self.pose(moved_joints).as_dict()
            pose_delta = {pose_key: moved[pose_key] - base[pose_key] for pose_key in POSE_KEYS}
            denom = actual_step if actual_step else 1.0
            position_delta_m = {axis: pose_delta[axis] for axis in ("x", "y", "z")}
            position_delta_mm = {axis: 1000.0 * position_delta_m[axis] for axis in ("x", "y", "z")}
            per_degree_mm = {
                axis: position_delta_mm[axis] / denom for axis in ("x", "y", "z")
            }
            rotation_delta_rad = {axis: pose_delta[axis] for axis in ("wx", "wy", "wz")}
            effects[key] = {
                "joint": name,
                "current_deg": current,
                "sample_step_deg": actual_step,
                "semantic": _semantic_effect(per_degree_mm, rotation_delta_rad),
                "position_delta_m": position_delta_m,
                "position_delta_mm": position_delta_mm,
                "rotation_delta_rad": rotation_delta_rad,
                "per_degree_mm": per_degree_mm,
                "moved_pose": moved,
            }

        return {
            "step_degrees_requested": step_deg,
            "pose_dependent": True,
            "coordinate_frame": "base_link",
            "target_frame": "gripper_frame_link",
            "current_pose": base,
            "effects": effects,
            "joint_limits": {
                key: {"min": lo, "max": hi} for key, (lo, hi) in JOINT_LIMITS.items()
            },
        }

    def solve(
        self,
        current_joints: dict[str, float],
        pose: EEPose,
        *,
        gripper: float | None = None,
        orientation_weight: float = 0.01,
        iters: int = 12,
    ) -> dict[str, float]:
        import numpy as np
        from lerobot.utils.rotation import Rotation

        current_q = np.array([float(current_joints[f"{name}.pos"]) for name in ARM_JOINTS], dtype=float)
        desired = np.eye(4, dtype=float)
        desired[:3, :3] = Rotation.from_rotvec([pose.wx, pose.wy, pose.wz]).as_matrix()
        desired[:3, 3] = [pose.x, pose.y, pose.z]

        # LeRobot's inverse_kinematics runs a single placo iteration, which does
        # not converge from a far guess (tens of mm of error — measured 32 mm on a
        # 3 cm move). Feed the result back as the next guess until it settles;
        # ~8 iterations reaches sub-mm while a guess already at the solution stays put.
        target_q = current_q
        for _ in range(max(1, iters)):
            target_q = self.kinematics.inverse_kinematics(
                target_q,
                desired,
                orientation_weight=orientation_weight,
            )
        target = {f"{name}.pos": float(target_q[i]) for i, name in enumerate(ARM_JOINTS)}
        target["gripper.pos"] = (
            float(current_joints.get("gripper.pos", 0.0)) if gripper is None else float(gripper)
        )
        return clamp_action(target)

    def offset_pose(
        self,
        current: EEPose,
        *,
        dx: float = 0.0,
        dy: float = 0.0,
        dz: float = 0.0,
        dwx: float = 0.0,
        dwy: float = 0.0,
        dwz: float = 0.0,
        max_step_m: float = 0.04,
    ) -> EEPose:
        import numpy as np

        delta = np.array([dx, dy, dz], dtype=float)
        norm = float(np.linalg.norm(delta))
        clipped = delta
        if norm > max_step_m and norm > 0:
            clipped = delta * (max_step_m / norm)
        return EEPose(
            x=current.x + float(clipped[0]),
            y=current.y + float(clipped[1]),
            z=current.z + float(clipped[2]),
            wx=current.wx + float(dwx),
            wy=current.wy + float(dwy),
            wz=current.wz + float(dwz),
            matrix=current.matrix,
        )


_SO101_KINEMATICS: SO101Kinematics | None = None


def so101_kinematics() -> SO101Kinematics:
    global _SO101_KINEMATICS
    if _SO101_KINEMATICS is None:
        _SO101_KINEMATICS = SO101Kinematics()
    return _SO101_KINEMATICS


def _semantic_effect(per_degree_mm: dict[str, float], rotation_delta_rad: dict[str, float]) -> str:
    axes = sorted(per_degree_mm.items(), key=lambda item: abs(item[1]), reverse=True)
    primary_axis, primary_mm = axes[0]
    secondary_axis, secondary_mm = axes[1]
    rotation_mag = sum(v * v for v in rotation_delta_rad.values()) ** 0.5
    translation_mag = sum(v * v for v in per_degree_mm.values()) ** 0.5

    direction = "positive" if primary_mm >= 0 else "negative"
    parts = [f"mostly {direction} {primary_axis} translation ({primary_mm:+.2f} mm/deg)"]
    if abs(secondary_mm) >= max(0.5, abs(primary_mm) * 0.35):
        secondary_direction = "positive" if secondary_mm >= 0 else "negative"
        parts.append(
            f"with {secondary_direction} {secondary_axis} coupling ({secondary_mm:+.2f} mm/deg)"
        )
    if rotation_mag > 0.02 and rotation_mag * 1000 > translation_mag:
        parts.append("orientation-dominant")
    elif rotation_mag > 0.02:
        parts.append("also rotates the claw")
    return "; ".join(parts)
