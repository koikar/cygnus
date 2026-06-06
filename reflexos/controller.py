"""The antifragility control loop.

For each episode toward a goal:

1. **Recall** a reflex for the situation. Hit → replay it (System-1, fast).
   Miss → run the fixed *habit* (the only thing a blind System-1 knows).
2. **Detect** a black swan in the result.
3. On a swan, **deliberate** (System-2): the reasoner perceives the scene and
   plans a recovery; execute it.
4. If the recovery succeeds, **learn** it — keyed by the situation signature, so
   the *next* occurrence is a fast recall, not another escalation.

The dropping escalation/cost over repeated swans is the antifragility curve.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .cognition.backend import CognitiveBackend
from .detector import BlackSwanDetector, situation_signature
from .poses import grasp_and_place_plan
from .robot.base import RobotBackend
from .safety import sanitize_call
from .types import Observation, Plan

DEFAULT_GOAL = "place the cube in the bin"

# The arm's blind habit: it was "trained" for a cube in zone A and does this
# regardless of where the cube actually is.
HABIT_PLAN: Plan = grasp_and_place_plan("A")


@dataclass
class EpisodeResult:
    episode: int
    signature: str
    cube_zone: str | None
    mode: str            # "reflex" (recall hit) | "habit" (blind default)
    escalated: bool      # did System-2 have to step in?
    success: bool
    tool_calls: int      # System-1 calls executed
    recovery_calls: int  # extra System-2 calls executed
    rationale: str

    def as_dict(self) -> dict:
        return asdict(self)


class Controller:
    def __init__(
        self,
        robot: RobotBackend,
        cognition: CognitiveBackend,
        detector: BlackSwanDetector | None = None,
        goal: str = DEFAULT_GOAL,
    ) -> None:
        self.robot = robot
        self.cognition = cognition
        self.detector = detector or BlackSwanDetector()
        self.goal = goal

    def _execute(self, plan: Plan) -> int:
        """Run a plan against the robot, returning the number of tool calls."""
        for raw in plan:
            call = sanitize_call(raw)  # guardrails before the body ever moves
            tool = call["tool"]
            args = call.get("args", {})
            if tool == "move_to":
                self.robot.move_to(args["target"])
            elif tool == "grip":
                self.robot.grip(args["mode"])
            elif tool == "home":
                self.robot.home()
            elif tool in ("look", "get_state"):
                self.robot.get_observation()
            else:
                raise ValueError(f"unknown tool in plan: {tool!r}")
        return len(plan)

    def run_episode(self, episode: int) -> EpisodeResult:
        before: Observation = self.robot.get_observation()
        zone = before.scene.get("cube_zone")
        signature = situation_signature(self.goal, before.scene)

        corrective = self.cognition.recall(signature)
        if corrective is not None:
            mode, plan = "reflex", corrective.plan
        else:
            mode, plan = "habit", HABIT_PLAN

        calls = self._execute(plan)
        after = self.robot.get_observation()

        swan = self.detector.check(self.goal, before, after)
        if swan is None:
            note = "recall hit → reflex" if mode == "reflex" else "habit succeeded"
            return EpisodeResult(
                episode=episode,
                signature=signature,
                cube_zone=zone,
                mode=mode,
                escalated=False,
                success=True,
                tool_calls=calls,
                recovery_calls=0,
                rationale=note,
            )

        # --- Black swan: escalate to System-2 -------------------------------
        decision = self.cognition.deliberate(after, self.goal)
        recovery_calls = self._execute(decision.plan)
        recovered = self.robot.get_observation()
        success = self.detector.is_success(recovered)

        self.cognition.learn(signature, decision, "recovered" if success else "failed")

        return EpisodeResult(
            episode=episode,
            signature=signature,
            cube_zone=zone,
            mode=mode,
            escalated=True,
            success=success,
            tool_calls=calls,
            recovery_calls=recovery_calls,
            rationale=decision.rationale,
        )
