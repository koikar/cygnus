"""``LocalBackend`` — self-contained cognition: SQLite memory + a reasoner.

Runs entirely offline. This is the local training fallback: a flaky venue network
can never freeze the arm, because recall and deliberation work without it.
"""

from __future__ import annotations

from typing import Optional

from ..memory import MemoryStore
from ..types import Corrective, Decision, Observation
from .reasoning import Reasoner, build_reasoner


class LocalBackend:
    name = "local"

    def __init__(self, db_path: str = ":memory:", reasoner: Optional[Reasoner] = None) -> None:
        self.memory = MemoryStore(db_path)
        self.reasoner = reasoner or build_reasoner()

    def recall(self, signature: str) -> Optional[Corrective]:
        return self.memory.get(signature)

    def deliberate(self, observation: Observation, goal: str) -> Decision:
        return self.reasoner.deliberate(observation, goal)

    def learn(self, signature: str, decision: Decision, outcome: str) -> None:
        self.memory.log_rationale(signature, decision.rationale, outcome)
        if outcome == "recovered":
            # Only validated recoveries become reflexes.
            self.memory.upsert(signature, decision.plan, decision.rationale)
