"""The antifragility claim, as an executable test.

A novel cube zone (a black swan) must escalate to System-2 exactly once; the
very next occurrence of the same situation must be a fast System-1 reflex with
no escalation and lower cost. All episodes must still succeed.
"""

import pytest

from cygnus import poses, skills
from cygnus.cognition import build_cognition
from cygnus.controller import Controller
from cygnus.detector import BlackSwanDetector
from cygnus.kinematics import so101_kinematics
from cygnus.robot import SimBackend
from cygnus.skill_audit import audit_skills


def run_scenario(scenario):
    robot = SimBackend()
    robot.connect()
    controller = Controller(robot, build_cognition("local"), BlackSwanDetector())
    results = []
    for i, zone in enumerate(scenario, start=1):
        robot.reset(cube_zone=zone)
        results.append(controller.run_episode(i))
    robot.disconnect()
    return results


def test_novel_zone_escalates_once_then_becomes_reflex():
    r = run_scenario(["B", "B"])
    assert all(ep.success for ep in r)

    first, second = r
    assert first.escalated is True and first.mode == "habit"
    assert second.escalated is False and second.mode == "reflex"
    # The learned reflex is strictly cheaper than the escalated recovery.
    assert (second.tool_calls + second.recovery_calls) < (first.tool_calls + first.recovery_calls)


def test_habit_zone_needs_no_escalation():
    (only,) = run_scenario(["A"])
    assert only.success and only.escalated is False and only.mode == "habit"


def test_escalations_fall_to_zero_over_repeats():
    r = run_scenario(["A", "B", "B", "C", "C", "B"])
    assert all(ep.success for ep in r)
    # One escalation per distinct novel zone (B, C); repeats are reflexes.
    assert sum(1 for ep in r if ep.escalated) == 2


def test_so101_kinematics_round_trips_current_pose():
    pytest.importorskip("placo")  # Cartesian IK needs placo (the `kinematics` extra)
    joints = {
        "shoulder_pan.pos": 59.0,
        "shoulder_lift.pos": -1.5,
        "elbow_flex.pos": 41.0,
        "wrist_flex.pos": 55.0,
        "wrist_roll.pos": 0.0,
        "gripper.pos": 60.0,
    }
    kin = so101_kinematics()
    pose = kin.pose(joints)
    solved = kin.solve(joints, pose, gripper=joints["gripper.pos"])

    for key, value in joints.items():
        assert abs(solved[key] - value) < 1e-6


def test_so101_joint_effects_ground_servo_degrees_in_claw_motion():
    pytest.importorskip("placo")  # Cartesian IK needs placo (the `kinematics` extra)
    joints = {
        "shoulder_pan.pos": 59.0,
        "shoulder_lift.pos": -34.0,
        "elbow_flex.pos": 80.0,
        "wrist_flex.pos": 14.0,
        "wrist_roll.pos": 0.0,
        "gripper.pos": 60.0,
    }
    effects = so101_kinematics().joint_effects(joints, step_deg=1.0)["effects"]

    # At this clear/retracted pose, +shoulder_lift lowers the claw in base Z.
    assert effects["shoulder_lift.pos"]["per_degree_mm"]["z"] < -1.0
    # Base pan and wrist roll are orientation-heavy, not clean vertical controls.
    assert abs(effects["shoulder_pan.pos"]["per_degree_mm"]["z"]) < 0.5
    assert abs(effects["wrist_roll.pos"]["per_degree_mm"]["z"]) < 0.5
    # Gripper commands articulate the jaw, not the FK end-effector frame.
    assert effects["gripper.pos"]["per_degree_mm"] == {"x": 0.0, "y": 0.0, "z": 0.0}


def test_home_is_harness_rest_with_ceiling_camera_attitude():
    pytest.importorskip("placo")
    assert poses.HOME == {
        "shoulder_pan.pos": 0.0,
        "shoulder_lift.pos": -45.0,
        "elbow_flex.pos": 95.0,
        "wrist_flex.pos": -70.0,
        "wrist_roll.pos": 0.0,
        "gripper.pos": 60.0,
    }
    pose = so101_kinematics().pose(poses.HOME)

    # Folded back over the harness/base, not neutral-straight in front.
    assert pose.x < 0.28
    assert pose.z > 0.14


def test_tabletop_grab_skill_uses_wrist_flex_not_roll():
    grab = skills.load_skill("tabletop_grab_pose_flex_down")
    target = grab["steps"][0]["args"]["target"]

    assert target["wrist_flex.pos"] > 25.0
    assert abs(target["wrist_roll.pos"]) < 1.0
    assert target["gripper.pos"] == poses.OPEN_GRIP

    demo = skills.load_skill("home_reach_grab_home_demo")
    tools = [step["tool"] for step in demo["steps"]]
    assert tools == ["move_to", "move_to", "move_to", "set_gripper", "set_gripper", "move_to"]
    assert demo["steps"][0]["args"]["target"] == poses.HOME
    assert demo["steps"][-1]["args"]["target"] == poses.HOME


def test_saved_robot_skills_match_current_body_schema():
    audit = audit_skills()
    assert audit["ok"], audit
    assert not audit["warnings"], audit
