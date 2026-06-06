"""Core data types shared across ReflexOS.

Joint and action keys follow the LeRobot convention ``"<joint>.pos"`` so the
same dicts flow unchanged between the simulator, the real SO-101 backend, and
the MCP tool surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# SO-101 is a 6-DOF arm. These are the joint names; runtime keys add ".pos".
JOINTS: list[str] = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]

# A single tool invocation, e.g. {"tool": "move_to", "args": {"target": {...}}}.
# A "plan" (a reflex or a recovery) is just an ordered list of these.
ToolCall = dict[str, Any]
Plan = list[ToolCall]


@dataclass
class Observation:
    """A snapshot of the arm + world, as the controller and reasoner see it.

    ``scene`` is the structured perception layer: in simulation it is ground
    truth; on the real arm it is derived from the camera frame (vision). Keeping
    it abstract means System-2 reasoning is identical in sim and on hardware.
    """

    joints: dict[str, float]
    scene: dict[str, Any] = field(default_factory=dict)
    frame: Optional[Any] = None  # primary camera ndarray (real hardware); None in sim
    frames: dict[str, Any] = field(default_factory=dict)  # all named camera frames
    grasped: Optional[bool] = None
    note: str = ""


@dataclass
class Decision:
    """The output of System-2 deliberation (or a recalled reflex)."""

    plan: Plan
    rationale: str
    source: str = "system2"  # "system2" | "reflex"


@dataclass
class Corrective:
    """A validated recovery stored in memory, keyed by a situation signature.

    Once stored, recalling it turns a former black swan into a System-1 reflex.
    """

    signature: str
    plan: Plan
    rationale: str
    success_count: int = 0
