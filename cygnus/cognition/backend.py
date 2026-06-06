"""The ``CognitiveBackend`` interface: the durable mind behind the robot body."""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from ..types import Corrective, Decision, Observation


@runtime_checkable
class CognitiveBackend(Protocol):
    name: str

    def recall(self, signature: str) -> Optional[Corrective]:
        """Return a previously-learned reflex for this situation, if any."""

    def deliberate(self, observation: Observation, goal: str) -> Decision:
        """System-2: reason over the scene and produce a recovery plan + rationale."""

    def learn(self, signature: str, decision: Decision, outcome: str) -> None:
        """Persist a validated recovery so it becomes a future reflex; log the rationale."""
