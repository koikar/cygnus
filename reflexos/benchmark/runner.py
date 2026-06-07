"""Eval runner for the pick-and-place benchmark.

Runs N seeded episodes through a policy, scores each against ground truth, and
writes one trace bundle per episode plus an aggregate scorecard. This is the
offline, no-LLM proof that the loop works and that *harness components matter*:
the `blind` policy ignores perception (a stand-in for "memory/skills off") and
fails whenever the cube is not where it assumes; the `skilled` policy reads the
observation and verifies its grasp (a stand-in for the full harness). The gap
between their success curves is the value the flywheel is supposed to add.

Usage:
  python -m reflexos.benchmark run --episodes 30 --policy skilled
  python -m reflexos.benchmark run --episodes 30 --policy blind --grasp-reliability 0.7
  python -m reflexos.benchmark compare --episodes 50   # run both, print the delta
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .pickplace import EnvConfig, PickPlaceEnv

OUT = Path("outputs/benchmark")


def _carry_to_bucket(env: PickPlaceEnv, target_bucket: str) -> None:
    env.home()
    env.move_to(f"bucket:{target_bucket}")
    env.set_gripper("open")  # release / deliver
    env.home()


def policy_blind(env: PickPlaceEnv, assume_pos: int = 4) -> None:
    """Ignores perception: always tries the cube at a fixed position. Fails when
    the cube spawned elsewhere — the 'open-loop, no memory' failure mode."""
    obs = env.observe()
    env.move_to(f"pos:{assume_pos}")
    env.set_gripper("closed")
    _carry_to_bucket(env, obs["target_bucket"])


def policy_skilled(env: PickPlaceEnv, max_retries: int = 3) -> None:
    """Reads the scene (perception/memory), grabs at the cube's actual position,
    and verifies the grasp before carrying — retrying on a slip. The full-harness
    behaviour: perceive -> act -> verify -> recover."""
    obs = env.observe()
    cube = obs["cube_location"]                 # e.g. "pos:3"
    target = obs["target_bucket"]
    if not cube.startswith("pos:"):
        return  # cube already lost; nothing to do
    for _ in range(max_retries):
        env.move_to(cube)
        env.set_gripper("closed")
        if env.observe()["holding"]:            # verify (lift-and-check analogue)
            break
        env.set_gripper("open")                 # reset jaws and retry
    _carry_to_bucket(env, target)


POLICIES: dict[str, Callable[[PickPlaceEnv], None]] = {
    "blind": policy_blind,
    "skilled": policy_skilled,
}


def run_episode(policy: str, seed: int, config: EnvConfig) -> dict:
    env = PickPlaceEnv(config)
    obs0 = env.reset(seed=seed)
    POLICIES[policy](env)
    result = env.score()
    return {
        "seed": seed,
        "policy": policy,
        "task": {"cube_position": obs0["cube_location"], "target_bucket": obs0["target_bucket"]},
        "score": result,
        "trace": env.history,   # the episode's trace bundle (every tool call + obs)
    }


def run(policy: str, episodes: int, config: EnvConfig, write: bool = True) -> dict:
    runs = [run_episode(policy, seed, config) for seed in range(episodes)]
    successes = sum(r["score"]["success"] for r in runs)
    violations = sum(r["score"]["violation_count"] for r in runs)
    steps = sum(r["score"]["steps"] for r in runs)
    scorecard = {
        "policy": policy,
        "episodes": episodes,
        "success_rate": round(successes / episodes, 3) if episodes else 0.0,
        "successes": successes,
        "avg_steps": round(steps / episodes, 2) if episodes else 0.0,
        "policy_violations": violations,
        "grasp_reliability": config.grasp_reliability,
    }
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        with (OUT / f"{policy}_episodes.jsonl").open("w") as f:
            for r in runs:
                f.write(json.dumps(r) + "\n")
        (OUT / f"{policy}_scorecard.json").write_text(json.dumps(scorecard, indent=2))
    return scorecard
