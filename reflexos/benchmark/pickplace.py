"""Dependency-free tabletop pick-and-place benchmark environment.

A small, seeded state machine that mirrors the reflexos pick-and-place world: a
cube spawns at one of N positions, and the arm must pick it and deliver it to a
target bucket. It deliberately has **no physics engine, torch, or hardware** —
the value here is a clean, repeatable, ground-truth-scored task a tedi can drive
over MCP, which is exactly what the physical SO-101 could not give us
(``reset()`` and ``score()`` are the missing benchmark half).

Semantics mirror what we learned on the real arm:
- a grasp succeeds only when the gripper is aligned with the cube's position;
- opening over the *target* bucket delivers the cube (success);
- opening anywhere else drops the cube (a "black swan" the agent must recover from);
- routing between stops should pass through ``home`` (a policy-compliance signal).

``grasp_reliability < 1.0`` makes an aligned close occasionally slip, so the
benchmark can require a verify-and-retry loop — the simulated counterpart of the
lift-and-verify gate we needed on hardware.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

POSITIONS = [1, 2, 3, 4, 5, 6]
BUCKETS = ["left", "right", "front"]
HOME = "home"


@dataclass
class EnvConfig:
    positions: list[int] = field(default_factory=lambda: list(POSITIONS))
    buckets: list[str] = field(default_factory=lambda: list(BUCKETS))
    # P(grasp succeeds) when correctly aligned. <1.0 forces verify+retry behaviour.
    grasp_reliability: float = 1.0
    # Policy: route through `home` between two distinct non-home stops.
    require_home_between: bool = True
    max_steps: int = 40


class PickPlaceEnv:
    """Seeded pick-and-place world with ground-truth delivery scoring."""

    def __init__(self, config: EnvConfig | None = None) -> None:
        self.config = config or EnvConfig()
        self._rng = random.Random()
        self.reset(seed=0)

    # -- episode lifecycle -------------------------------------------------
    def reset(self, seed: int | None = None, task: dict[str, Any] | None = None) -> dict:
        """Start a fresh episode. ``seed`` makes the task reproducible; an explicit
        ``task`` ({"cube_position": N, "target_bucket": side}) overrides sampling."""
        if seed is not None:
            self._rng.seed(seed)
        if task:
            cube_pos = int(task["cube_position"])
            target = str(task["target_bucket"])
        else:
            cube_pos = self._rng.choice(self.config.positions)
            target = self._rng.choice(self.config.buckets)
        self.seed = seed
        self.target_bucket = target
        self.ee = HOME                       # end-effector location
        self.gripper = "open"
        self.holding = False
        self.cube_loc = f"pos:{cube_pos}"    # where the cube physically is
        self.delivered = False
        self.steps = 0
        self.violations: list[str] = []
        self.history: list[dict] = []
        self.done = False
        return self.observe()

    # -- perception --------------------------------------------------------
    def observe(self) -> dict:
        """Truthful perception of the scene (the tedi reads this each step)."""
        return {
            "ee_location": self.ee,
            "gripper": self.gripper,
            "holding": self.holding,
            "cube_location": self.cube_loc,
            "target_bucket": self.target_bucket,
            "delivered": self.delivered,
            "steps": self.steps,
            "done": self.done,
        }

    def targets(self) -> list[str]:
        return (
            [HOME]
            + [f"pos:{p}" for p in self.config.positions]
            + [f"bucket:{b}" for b in self.config.buckets]
        )

    # -- actions -----------------------------------------------------------
    def move_to(self, target: str) -> dict:
        self._tick()
        if target not in self.targets():
            return self._fail(f"unknown target {target!r}")
        if (
            self.config.require_home_between
            and self.ee != HOME
            and target != HOME
            and target != self.ee
        ):
            self.violations.append(f"moved {self.ee}->{target} without routing home")
        prev = self.ee
        self.ee = target
        if self.holding:  # the cube rides with the arm while held
            self.cube_loc = target
        return self._event("move_to", {"from": prev, "to": target})

    def set_gripper(self, state: str) -> dict:
        self._tick()
        if state not in ("open", "closed"):
            return self._fail(f"gripper must be 'open'|'closed', got {state!r}")
        prev = self.gripper
        self.gripper = state
        note: str | None = None
        if state == "closed" and prev != "closed":
            aligned = (not self.holding) and self.ee == self.cube_loc and self.ee.startswith("pos:")
            if aligned and self._rng.random() <= self.config.grasp_reliability:
                self.holding = True
                note = "grasped"
            elif aligned:
                note = "grasp_slipped"      # aligned but missed -> retry needed
            else:
                note = "closed_on_air"
        elif state == "open" and prev == "closed" and self.holding:
            self.holding = False
            self.cube_loc = self.ee
            if self.ee.startswith("bucket:"):
                self.delivered = True        # released into a bucket (any side)
                note = "delivered" if self.ee == f"bucket:{self.target_bucket}" else "delivered_wrong_bucket"
            else:
                note = "dropped_off_target"   # released off-target -> black swan
        return self._event("set_gripper", {"state": state, "note": note})

    def home(self) -> dict:
        return self.move_to(HOME)

    # -- scoring -----------------------------------------------------------
    def score(self) -> dict:
        """Ground-truth episode verdict. Success = cube delivered to the target bucket."""
        in_target = self.cube_loc == f"bucket:{self.target_bucket}"
        return {
            "success": bool(self.delivered and in_target),
            "delivered": self.delivered,
            "correct_bucket": in_target,
            "cube_location": self.cube_loc,
            "target_bucket": self.target_bucket,
            "steps": self.steps,
            "policy_violations": list(self.violations),
            "violation_count": len(self.violations),
        }

    # -- internals ---------------------------------------------------------
    def _tick(self) -> None:
        self.steps += 1
        if self.steps >= self.config.max_steps:
            self.done = True

    def _event(self, tool: str, data: dict) -> dict:
        rec = {"tool": tool, **data, "obs": self.observe()}
        self.history.append(rec)
        return rec

    def _fail(self, msg: str) -> dict:
        rec = {"tool": "error", "error": msg, "obs": self.observe()}
        self.history.append(rec)
        return rec
