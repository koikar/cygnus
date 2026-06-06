"""Reusable robot skills — recorded tool-call sequences (the System-1 reflexes).

A *skill* is an ordered list of tool calls (``move_to`` / ``grip`` / ``home``)
that together perform a task such as "pick up the blue cube" for a known object
position. Recording a taught sequence captures the exact joint waypoints **and**
the grip actions, so a whole multi-step action replays as a single call.

Skills are **open-loop**: a replay reproduces the recorded joint distances, so it
only succeeds while the target is in the position it was taught for. When the
world changes (the cube moved), replay misses — and *that* is the black swan that
triggers re-teaching/re-reasoning into a new skill. That capture → replay →
re-learn cycle is the antifragility loop.

Persistence: ``skills/<name>.json`` (the executable steps) plus a generated
``skills/<name>/SKILL.md`` following the ``skill://`` documentation convention,
so a skill can later be registered with a tedi as durable muscle memory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .types import Plan

SKILLS_DIR = Path(os.getenv("CYGNUS_SKILLS_DIR", "skills"))


def _skill_json(name: str) -> Path:
    return SKILLS_DIR / f"{name}.json"


def save_skill(name: str, steps: Plan, description: str = "", notes: str = "") -> dict:
    """Persist a skill (its steps) as JSON and write a companion SKILL.md."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    data = {"name": name, "description": description, "notes": notes, "steps": steps}
    _skill_json(name).write_text(json.dumps(data, indent=2))
    _write_skill_md(name, data)
    return data


def load_skill(name: str) -> dict:
    path = _skill_json(name)
    if not path.exists():
        raise FileNotFoundError(f"no skill named {name!r} in {SKILLS_DIR}")
    return json.loads(path.read_text())


def list_skills() -> list[dict]:
    """Return a compact index of saved skills (name, description, step count)."""
    if not SKILLS_DIR.exists():
        return []
    out = []
    for path in sorted(SKILLS_DIR.glob("*.json")):
        try:
            d = json.loads(path.read_text())
            out.append(
                {
                    "name": d.get("name", path.stem),
                    "description": d.get("description", ""),
                    "steps": len(d.get("steps", [])),
                }
            )
        except Exception:
            continue
    return out


def _step_str(step: dict[str, Any]) -> str:
    tool = step.get("tool", "?")
    args = step.get("args", {})
    if tool == "move_to":
        target = args.get("target", {})
        joints = ", ".join(f"{k.removesuffix('.pos')}={v:.1f}" for k, v in target.items())
        return f"`move_to` → {joints}"
    if tool == "move_relative":
        delta = args.get("delta", {})
        joints = ", ".join(f"{k.removesuffix('.pos')}={v:+.1f}" for k, v in delta.items())
        return f"`move_relative` → {joints}"
    if tool == "set_gripper":
        return f"`set_gripper` → {args.get('position')}"
    if tool == "grip":
        return f"`grip` → {args.get('mode')}"
    if tool == "wait_until_settled":
        return "`wait_until_settled`"
    return f"`{tool}` {args or ''}".strip()


def _write_skill_md(name: str, data: dict) -> None:
    steps = data.get("steps", [])
    lines = [
        f"# Skill: {name}",
        "",
        f"> {data.get('description') or 'Recorded robot motion skill.'}",
        "",
        f"**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** {len(steps)}",
        "",
        "## When to use",
        "",
        data.get("notes") or "Replays a taught pick/place motion for a known object position.",
        "",
        "## Procedure (recorded tool calls)",
        "",
    ]
    lines += [f"{i}. {_step_str(s)}" for i, s in enumerate(steps, 1)]
    lines += [
        "",
        "## Caveats",
        "",
        "Open-loop replay: valid only while the target is in the recorded position. "
        "If the object has moved, replay will miss the grasp — re-teach the skill "
        "(the black-swan → re-learn loop that makes the system antifragile).",
        "",
    ]
    skill_dir = SKILLS_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("\n".join(lines))
