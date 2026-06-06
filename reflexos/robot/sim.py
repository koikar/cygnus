"""A dependency-free simulator of the SO-101 pick-and-place world.

It models exactly enough physics to exercise the agent-training loop with no
hardware and no network:

* The arm has joints (in ``"<joint>.pos"`` form) that snap to commanded targets.
* A cube sits in one zone (A/B/C). The arm's *habit* is trained for zone A.
* ``grip("close")`` only grasps if the gripper is actually *at* the cube's zone.
  Closing on empty air (because a blind habit went to the wrong zone) is the
  novel case the detector catches.
* ``grip("open")`` over the bin places the cube → task success.
"""

from __future__ import annotations

from .. import poses
from ..safety import clamp_action
from ..types import Observation


class SimBackend:
    name = "sim"

    def __init__(self, cube_zone: str = "A") -> None:
        self.joints: dict[str, float] = {**poses.HOME, "gripper.pos": poses.OPEN_GRIP}
        self.cube_zone = cube_zone
        self.holding = False
        self.cube_in_bin = False
        self.connected = False

    # -- lifecycle ---------------------------------------------------------
    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def reset(self, cube_zone: str | None = None) -> None:
        """Start a fresh episode (optionally relocating the cube)."""
        if cube_zone is not None:
            self.cube_zone = cube_zone
        self.joints = {**poses.HOME, "gripper.pos": poses.OPEN_GRIP}
        self.holding = False
        self.cube_in_bin = False

    # -- perception --------------------------------------------------------
    def _scene(self) -> dict:
        return {
            "cube_zone": None if self.cube_in_bin else self.cube_zone,
            "cube_in_bin": self.cube_in_bin,
            "holding": self.holding,
            "bin": "BIN",
        }

    def get_observation(self) -> Observation:
        return Observation(
            joints=dict(self.joints),
            scene=self._scene(),
            frame=None,
            grasped=self.holding,
            note="simulated scene (ground truth)",
        )

    def look(self) -> Observation:
        return self.get_observation()

    # -- actuation ---------------------------------------------------------
    def move_to(self, target: dict[str, float]) -> Observation:
        self.joints.update(clamp_action(target))  # guardrails enforced here too
        return self.get_observation()

    def grip(self, mode: str) -> Observation:
        if mode == "close":
            at_cube = (
                not self.holding
                and not self.cube_in_bin
                and poses.near(self.joints, poses.ZONE_POSE[self.cube_zone])
            )
            self.holding = bool(at_cube)  # closing on empty air leaves holding False
            self.joints["gripper.pos"] = poses.CLOSED_GRIP
        elif mode == "open":
            if self.holding and poses.near(self.joints, poses.BIN_POSE):
                self.holding = False
                self.cube_in_bin = True
            else:
                self.holding = False  # released somewhere that isn't the bin
            self.joints["gripper.pos"] = poses.OPEN_GRIP
        else:
            raise ValueError(f"grip mode must be 'open' or 'close', got {mode!r}")
        return self.get_observation()

    def home(self) -> Observation:
        self.joints.update(poses.HOME)  # arm-only: homing preserves the gripper state
        return self.get_observation()
