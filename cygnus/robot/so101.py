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
        scene_camera_index: int = -1,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ) -> None:
        self.port = port
        self.id = id
        self.camera_index = camera_index          # wrist / eye-in-hand cam
        self.scene_camera_index = scene_camera_index  # optional distant/3rd-person cam
        self.width = width
        self.height = height
        self.fps = fps
        self._robot: Any = None

    def connect(self) -> None:
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

        # Cameras are optional: pass index < 0 to omit. `wrist` is the eye-in-hand
        # camera; `scene` is an optional distant/third-person view of the arm.
        # With no cameras, `look` returns state only, exactly like the simulator —
        # useful when the OS blocks camera access (e.g. macOS TCC) or none is wired.
        cameras = {}
        wanted = {"wrist": self.camera_index, "scene": self.scene_camera_index}
        if any(idx is not None and idx >= 0 for idx in wanted.values()):
            from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

            for cam_name, idx in wanted.items():
                if idx is not None and idx >= 0:
                    cameras[cam_name] = OpenCVCameraConfig(
                        index_or_path=idx,
                        width=self.width,
                        height=self.height,
                        fps=self.fps,
                    )
        config = SO101FollowerConfig(
            port=self.port,
            id=self.id,
            max_relative_target=None,
            cameras=cameras,
        )
        self._robot = SO101Follower(config)
        # Load the saved calibration (created by `lerobot-calibrate`); never run
        # interactive calibration from the server.
        self._robot.connect(calibrate=False)

    def disconnect(self) -> None:
        if self._robot is not None:
            self._robot.disconnect()
            self._robot = None

    def _split(self, obs: dict) -> Observation:
        """Split a LeRobot observation dict into joints + named camera frames."""
        joints = {k: float(v) for k, v in obs.items() if k.endswith(".pos")}
        # Camera frames are the non-".pos" entries that look like image arrays.
        frames = {
            k: v for k, v in obs.items() if not k.endswith(".pos") and hasattr(v, "shape")
        }
        frame = frames.get("wrist") or (next(iter(frames.values())) if frames else None)
        # TODO: derive a structured `scene` from the frames with a vision model.
        return Observation(
            joints=joints, scene={}, frame=frame, frames=frames, note="live SO-101"
        )

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
