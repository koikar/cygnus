"""The ``RobotBackend`` interface that every body implements.

The five verbs map one-to-one onto the MCP tool surface
(``look``/``get_state``/``move_to``/``grip``/``home``), so the agent operates a
simulated arm and a real arm through identical calls.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..types import Observation


@runtime_checkable
class RobotBackend(Protocol):
    name: str

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def get_observation(self) -> Observation:
        """Joint positions + structured scene (+ camera frame on real hardware)."""

    def look(self) -> Observation:
        """Capture the current scene/frame. In sim this equals ``get_observation``."""

    def move_to(self, target: dict[str, float]) -> Observation:
        """Move toward joint-space ``target`` (clamped to safe limits)."""

    def grip(self, mode: str) -> Observation:
        """``mode`` is ``"open"`` or ``"close"``."""

    def home(self) -> Observation:
        """Return to the safe neutral pose."""
