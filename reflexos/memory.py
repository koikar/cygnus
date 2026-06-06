"""Durable local memory for the ``LocalBackend``.

A tiny SQLite store of validated correctives (keyed by situation signature) and
a rationale log. Defaults to an in-memory database so demo and test runs start
fresh; pass a file path to persist learning across sessions.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Optional

from .types import Corrective, Plan

_SCHEMA = """
CREATE TABLE IF NOT EXISTS correctives (
    signature     TEXT PRIMARY KEY,
    plan_json     TEXT NOT NULL,
    rationale     TEXT NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS rationale_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    signature TEXT NOT NULL,
    rationale TEXT NOT NULL,
    outcome   TEXT NOT NULL
);
"""


class MemoryStore:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def get(self, signature: str) -> Optional[Corrective]:
        row = self.conn.execute(
            "SELECT * FROM correctives WHERE signature = ?", (signature,)
        ).fetchone()
        if row is None:
            return None
        return Corrective(
            signature=row["signature"],
            plan=json.loads(row["plan_json"]),
            rationale=row["rationale"],
            success_count=row["success_count"],
        )

    def upsert(self, signature: str, plan: Plan, rationale: str) -> None:
        """Store a corrective, or bump its success count if already known."""
        self.conn.execute(
            """
            INSERT INTO correctives (signature, plan_json, rationale, success_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(signature) DO UPDATE SET
                plan_json = excluded.plan_json,
                rationale = excluded.rationale,
                success_count = success_count + 1
            """,
            (signature, json.dumps(plan), rationale),
        )
        self.conn.commit()

    def log_rationale(self, signature: str, rationale: str, outcome: str) -> None:
        self.conn.execute(
            "INSERT INTO rationale_log (signature, rationale, outcome) VALUES (?, ?, ?)",
            (signature, rationale, outcome),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
