"""Real SO-101 follower arm via LeRobot 0.5.1.

Verified import path (0.5.1 unifies SO-100/SO-101 under ``so_follower``):

    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

LeRobot is imported lazily inside ``connect`` so that simulation and the test
suite never require the hardware stack. Vision/scene captioning is left as a
TODO — for the core demo the reasoner works off the structured scene, and on
hardware the raw frame is attached to the observation for a vision model.
"""

from __future__ import annotations

from typing import Any

from ..safety import clamp_action
from ..types import Observation


class SO101Backend:
    name = "so101"

    def __init__(
        self,
        port: str,
        id: str = "cygnus_follower",
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ) -> None:
        self.port = port
        self.id = id
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self._robot: Any = None

    def connect(self) -> None:
        from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

        config = SO101FollowerConfig(
            port=self.port,
            id=self.id,
            max_relative_target=None,
            cameras={
                "front": OpenCVCameraConfig(
                    index_or_path=self.camera_index,
                    width=self.width,
                    height=self.height,
                    fps=self.fps,
                )
            },
        )
        self._robot = SO101Follower(config)
        self._robot.connect(calibrate=True)

    def disconnect(self) -> None:
        if self._robot is not None:
            self._robot.disconnect()
            self._robot = None

    def _split(self, obs: dict) -> Observation:
        """Split a LeRobot observation dict into joints + camera frame."""
        joints = {k: float(v) for k, v in obs.items() if k.endswith(".pos")}
        frame = obs.get("front")
        # TODO: derive a structured `scene` from `frame` with a vision model.
        return Observation(joints=joints, scene={}, frame=frame, note="live SO-101")

    def get_observation(self) -> Observation:
        return self._split(self._robot.get_observation())

    def look(self) -> Observation:
        return self.get_observation()

    def move_to(self, target: dict[str, float]) -> Observation:
        self._robot.send_action(clamp_action(target))
        return self.get_observation()

    def grip(self, mode: str) -> Observation:
        from .. import poses

        if mode not in {"open", "close"}:
            raise ValueError(f"grip mode must be 'open' or 'close', got {mode!r}")
        value = poses.CLOSED_GRIP if mode == "close" else poses.OPEN_GRIP
        self._robot.send_action({"gripper.pos": value})
        return self.get_observation()

    def home(self) -> Observation:
        from .. import poses

        self._robot.send_action(clamp_action(poses.HOME))
        return self.get_observation()
