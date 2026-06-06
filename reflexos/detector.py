"""The black-swan detector.

It watches observations for the signatures of a rare manipulation failure:
a grasp that closed on empty air, a joint that didn't reach its target, or a
goal that simply wasn't met. When one fires, the controller escalates from
System-1 reflex to System-2 deliberation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import Observation


@dataclass
class Swan:
    """A detected anomaly: what went wrong, and a stable key to learn against."""

    kind: str          # "task_unmet" | "empty_grasp" | "joint_stall"
    signature: str     # situation key used for recall/learning
    detail: str


def situation_signature(goal: str, scene: dict) -> str:
    """Stable key for a situation, used to recall a matching reflex."""
    return f"{goal}|cube@{scene.get('cube_zone')}"


class BlackSwanDetector:
    def is_success(self, obs: Observation) -> bool:
        """Task is met when the cube is in the bin."""
        return bool(obs.scene.get("cube_in_bin"))

    def check(self, goal: str, before: Observation, after: Observation) -> Swan | None:
        """Return a Swan if the attempt failed, else None.

        ``before`` carries the situation at episode start (used for the
        signature even after the cube's reported zone changes).
        """
        if self.is_success(after):
            return None

        sig = situation_signature(goal, before.scene)

        # Closed the gripper but came away empty → classic missed grasp.
        if after.grasped is False and after.scene.get("cube_zone") is not None:
            return Swan(
                kind="empty_grasp",
                signature=sig,
                detail="gripper closed but nothing was grasped",
            )

        return Swan(
            kind="task_unmet",
            signature=sig,
            detail="goal not achieved after the attempt",
        )
