"""System-2 reasoners — the model that looks at a failure and plans a recovery.

Two implementations behind one ``Reasoner`` interface:

* ``ScriptedReasoner`` — deterministic, offline, no API key. It "perceives" the
  cube's true zone from the scene and re-plans toward it. This is what makes the
  antifragility demo runnable on a laptop with nothing configured.
* ``LLMReasoner`` — the online path. Sends the scene + goal + available zones to
  a vision-capable chat model (Azure OpenAI or OpenAI) and asks which zone the
  cube is in. The plan itself is constructed locally from the named-pose table,
  so the safety guardrails always apply regardless of what the model returns.

``build_reasoner()`` picks the LLM path when credentials are present, else falls
back to scripted.
"""

from __future__ import annotations

import json
import os
from typing import Protocol

from .. import poses
from ..types import Decision, Observation


class Reasoner(Protocol):
    name: str

    def deliberate(self, observation: Observation, goal: str) -> Decision: ...


class ScriptedReasoner:
    """A stand-in for a reasoning model: perceives the cube zone and re-plans."""

    name = "scripted"

    def deliberate(self, observation: Observation, goal: str) -> Decision:
        zone = observation.scene.get("cube_zone")
        if zone not in poses.ZONE_POSE:
            # Nothing actionable perceived — return the habitual plan as a guess.
            return Decision(
                plan=poses.grasp_and_place_plan("A"),
                rationale="Could not localize the cube; falling back to the habitual approach.",
                source="system2",
            )
        rationale = (
            f"Perceived the cube in zone {zone}, not the habitual zone A. "
            f"Re-approaching zone {zone} with an open gripper before grasping, "
            f"then placing in the bin."
        )
        return Decision(plan=poses.grasp_and_place_plan(zone), rationale=rationale, source="system2")


_SYSTEM_PROMPT = (
    "You operate a robot arm doing pick-and-place. Given a description of the "
    "scene and the goal, identify which zone the cube is in. Valid zones: "
    f"{sorted(poses.ZONE_POSE)}. Respond ONLY with compact JSON: "
    '{\"zone\": \"<zone>\", \"rationale\": \"<one sentence>\"}.'
)


class LLMReasoner:
    """Online System-2 via Azure OpenAI or OpenAI chat completions.

    The model decides *which zone*; the executable plan is built locally so the
    safety guardrails are never delegated to the model.
    """

    name = "llm"

    def __init__(self, client, model: str) -> None:
        self.client = client
        self.model = model

    def deliberate(self, observation: Observation, goal: str) -> Decision:
        scene_text = json.dumps(observation.scene)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Goal: {goal}\nScene: {scene_text}"},
        ]
        # NOTE: when a real camera frame is available, attach it here as an
        # image content part so a vision-capable deployment can perceive directly.
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        zone = data.get("zone", "A")
        rationale = data.get("rationale", f"Model selected zone {zone}.")
        if zone not in poses.ZONE_POSE:
            zone = "A"
        return Decision(plan=poses.grasp_and_place_plan(zone), rationale=rationale, source="system2")


def build_reasoner() -> Reasoner:
    """LLM reasoner if credentials are configured, otherwise the scripted one."""
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_key = os.getenv("OPENAI_API_KEY")
    try:
        if azure_key and azure_endpoint:
            from openai import AzureOpenAI

            client = AzureOpenAI(
                api_key=azure_key,
                azure_endpoint=azure_endpoint,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            )
            model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.5")
            return LLMReasoner(client, model)
        if openai_key:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            return LLMReasoner(client, os.getenv("OPENAI_MODEL", "gpt-4o"))
    except Exception:
        # Any import/auth issue → stay fully functional offline.
        pass
    return ScriptedReasoner()
