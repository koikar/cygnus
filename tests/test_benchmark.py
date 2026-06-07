"""Tests for the pick-and-place benchmark env, policies, and scoring."""

from __future__ import annotations

from reflexos.benchmark import EnvConfig, PickPlaceEnv
from reflexos.benchmark.runner import run, run_episode


def test_reset_is_seed_reproducible():
    a = PickPlaceEnv().reset(seed=42)
    b = PickPlaceEnv().reset(seed=42)
    assert a["cube_location"] == b["cube_location"]
    assert a["target_bucket"] == b["target_bucket"]


def test_explicit_task_overrides_sampling():
    env = PickPlaceEnv()
    obs = env.reset(task={"cube_position": 3, "target_bucket": "left"})
    assert obs["cube_location"] == "pos:3"
    assert obs["target_bucket"] == "left"


def test_clean_pick_and_place_succeeds():
    env = PickPlaceEnv()
    env.reset(task={"cube_position": 2, "target_bucket": "right"})
    env.move_to("pos:2")
    assert env.set_gripper("closed")["note"] == "grasped"
    env.home()
    env.move_to("bucket:right")
    assert env.set_gripper("open")["note"] == "delivered"
    score = env.score()
    assert score["success"] and score["correct_bucket"]


def test_grasp_requires_alignment():
    env = PickPlaceEnv()
    env.reset(task={"cube_position": 5, "target_bucket": "left"})
    env.move_to("pos:1")  # wrong position
    assert env.set_gripper("closed")["note"] == "closed_on_air"
    assert not env.observe()["holding"]


def test_wrong_bucket_is_not_success():
    env = PickPlaceEnv()
    env.reset(task={"cube_position": 4, "target_bucket": "left"})
    env.move_to("pos:4")
    env.set_gripper("closed")
    env.home()
    env.move_to("bucket:right")  # wrong side
    env.set_gripper("open")
    score = env.score()
    assert score["delivered"] and not score["correct_bucket"]
    assert not score["success"]


def test_route_home_policy_violation():
    env = PickPlaceEnv()
    env.reset(task={"cube_position": 1, "target_bucket": "front"})
    env.move_to("pos:1")
    env.move_to("pos:2")  # pos->pos without home == violation
    assert env.score()["violation_count"] >= 1


def test_skilled_policy_beats_blind_under_random_tasks():
    config = EnvConfig()
    blind = run("blind", episodes=30, config=config, write=False)
    skilled = run("skilled", episodes=30, config=config, write=False)
    # blind assumes pos 4, so it fails most randomized episodes; skilled perceives.
    assert skilled["success_rate"] > blind["success_rate"]
    assert skilled["success_rate"] >= 0.95


def test_skilled_recovers_from_unreliable_grasp():
    # aligned grasp slips sometimes; verify+retry should still deliver.
    config = EnvConfig(grasp_reliability=0.6)
    r = run_episode("skilled", seed=7, config=config)
    assert r["score"]["success"]
