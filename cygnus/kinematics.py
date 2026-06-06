"""SO-101 end-effector kinematics.

This wraps LeRobot's placo-backed ``RobotKinematics`` behind a small local API
that speaks Cygnus joint dictionaries. Imports stay lazy so the simulator and
tests do not require the hardware stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .safety import clamp_action
from .types import JOINTS

ARM_JOINTS = [name for name in JOINTS if name != "gripper"]
URDF_PATH = Path(__file__).parent / "assets" / "so101" / "so101_kinematics.urdf"


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
