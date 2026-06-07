"""Audit saved robot skills against the current learned body schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import poses, skills
from .safety import JOINT_LIMITS, is_within_limits

REQUIRED_SKILLS = {
    "home",
    "reach_forward_home_height_x044",
    "tabletop_grab_pose_flex_down",
    "tabletop_grab_flex_down_close_open",
    "home_reach_grab_home_demo",
}
ALLOWED_TOOLS = {
    "move_to",
    "move_relative",
    "move_ee_to",
    "move_ee_by",
    "set_gripper",
    "grip",
    "home",
    "wait_until_settled",
    "verify_grasp",
    "skill",
}


def audit_skills(skills_dir: Path = skills.SKILLS_DIR) -> dict[str, Any]:
    """Return machine-readable errors/warnings for the saved skill catalog."""
    errors: list[str] = []
    warnings: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}

    if not skills_dir.exists():
        errors.append(f"missing skills directory: {skills_dir}")
        return _result(loaded, errors, warnings)

    for path in sorted(skills_dir.glob("*.json")):
        try:
            data = skills.load_skill(path.stem)
        except Exception as exc:
            errors.append(f"{path.name}: cannot load skill: {exc}")
            continue
        name = str(data.get("name", ""))
        loaded[name] = data
        if name != path.stem:
            errors.append(f"{path.name}: name field {name!r} does not match filename")
        if not (skills_dir / name / "SKILL.md").exists():
            errors.append(f"{name}: missing companion SKILL.md")
        _audit_steps(name, data.get("steps", []), errors, warnings)

    for name in sorted(REQUIRED_SKILLS - set(loaded)):
        errors.append(f"missing required skill: {name}")
    for name in sorted(loaded):
        lowered = name.lower()
        if "roll" in lowered and "grab" in lowered:
            errors.append(f"{name}: tabletop grabbing must use wrist_flex, not wrist_roll")

    _audit_goal_skills(loaded, errors, warnings)
    return _result(loaded, errors, warnings)


def _audit_steps(
    name: str,
    steps: Any,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(steps, list) or not steps:
        errors.append(f"{name}: steps must be a non-empty list")
        return
    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"{name}: step {i} is not an object")
            continue
        tool = step.get("tool")
        args = step.get("args", {})
        if tool not in ALLOWED_TOOLS:
            errors.append(f"{name}: step {i} uses unsupported tool {tool!r}")
        if tool == "move_to":
            target = args.get("target", {})
            if not isinstance(target, dict) or not target:
                errors.append(f"{name}: step {i} move_to missing target")
            elif not is_within_limits(target):
                errors.append(f"{name}: step {i} move_to target outside joint limits")
            unknown = sorted(set(target) - set(JOINT_LIMITS))
            if unknown:
                errors.append(f"{name}: step {i} move_to target has unknown joints {unknown}")
        if tool == "move_relative":
            delta = args.get("delta", {})
            if not isinstance(delta, dict) or not delta:
                errors.append(f"{name}: step {i} move_relative missing delta")
            unknown = sorted(set(delta) - set(JOINT_LIMITS))
            if unknown:
                errors.append(f"{name}: step {i} move_relative delta has unknown joints {unknown}")
        if tool == "skill":
            ref = args.get("name")
            if not ref or not isinstance(ref, str):
                errors.append(f"{name}: step {i} skill reference missing name")
            elif not (skills.SKILLS_DIR / f"{ref}.json").exists():
                errors.append(f"{name}: step {i} references unknown skill {ref!r}")
        if tool == "set_gripper":
            position = args.get("position")
            if position is None:
                errors.append(f"{name}: step {i} set_gripper missing position")
            elif not is_within_limits({"gripper.pos": float(position)}):
                errors.append(f"{name}: step {i} gripper position outside limits")
        tolerance = args.get("tolerance")
        if tool in {"move_to", "move_relative", "move_ee_to", "move_ee_by"} and tolerance:
            if float(tolerance) > 2.0 and name in REQUIRED_SKILLS:
                warnings.append(f"{name}: step {i} tolerance {tolerance} is loose for a goal skill")


def _audit_goal_skills(
    loaded: dict[str, dict[str, Any]],
    errors: list[str],
    warnings: list[str],
) -> None:
    home = _first_target(loaded.get("home"))
    if home and home != poses.HOME:
        errors.append("home skill target differs from poses.HOME")

    grab = _first_target(loaded.get("tabletop_grab_pose_flex_down"))
    if grab:
        if grab.get("wrist_flex.pos", 0) <= 25:
            errors.append("tabletop_grab_pose_flex_down must pitch downward with wrist_flex > 25")
        if abs(float(grab.get("wrist_roll.pos", 999))) >= 1:
            errors.append("tabletop_grab_pose_flex_down must keep wrist_roll near neutral")
        if grab.get("gripper.pos") != poses.OPEN_GRIP:
            errors.append("tabletop_grab_pose_flex_down must start with the gripper open")

    demo = loaded.get("home_reach_grab_home_demo")
    if demo:
        steps = demo.get("steps", [])
        tools = [step.get("tool") for step in steps]
        if tools != ["move_to", "move_to", "move_to", "set_gripper", "set_gripper", "move_to"]:
            errors.append("home_reach_grab_home_demo must be home, reach, grab-pose, close, open, home")
        if steps and steps[0].get("args", {}).get("target") != poses.HOME:
            errors.append("home_reach_grab_home_demo must start at poses.HOME")
        if steps and steps[-1].get("args", {}).get("target") != poses.HOME:
            errors.append("home_reach_grab_home_demo must end at poses.HOME")


def _first_target(skill: dict[str, Any] | None) -> dict[str, float] | None:
    if not skill:
        return None
    steps = skill.get("steps", [])
    if not steps:
        return None
    target = steps[0].get("args", {}).get("target")
    return target if isinstance(target, dict) else None


def _result(
    loaded: dict[str, dict[str, Any]],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "ok": not errors,
        "skill_count": len(loaded),
        "skills": sorted(loaded),
        "required_skills": sorted(REQUIRED_SKILLS),
        "errors": errors,
        "warnings": warnings,
    }
