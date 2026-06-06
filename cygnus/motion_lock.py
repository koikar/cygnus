"""Process-wide actuation lock — serialize robot motion across concurrent clients.

Two MCP clients (e.g. Claude + Codex, or several tedis) can reach the same robot
server. Without serialization their ``move_to`` / ``move_ee_*`` / ``grip`` calls
interleave on **one physical arm** — jerky at best, dangerous at worst. This is a
single re-entrant guard: actuation tools wrap ``motion_lock()``; only one motion
runs at a time, others wait up to ``timeout`` then fail closed with ``MotionBusy``.

FastMCP runs sync tool handlers in a worker thread, so a ``threading.Lock``
correctly serializes concurrent tool calls. Read-only tools (``look``,
``get_state``) must NOT take the lock — they may run concurrently.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager

_LOCK = threading.Lock()
_holder: dict[str, str | None] = {"owner": None}


class MotionBusy(RuntimeError):
    """Raised when the arm is already executing a motion for another caller."""


@contextmanager
def motion_lock(owner: str = "mcp", timeout: float = 5.0):
    """Hold the single actuation lock for the duration of one motion command.

    Wrap every hardware-moving tool with this. Concurrent callers block up to
    ``timeout`` seconds, then get ``MotionBusy`` (fail closed) rather than
    interleaving commands on the arm.
    """
    acquired = _LOCK.acquire(timeout=timeout)
    if not acquired:
        raise MotionBusy(
            f"arm is busy executing a motion (owner={_holder['owner']}); retry shortly"
        )
    _holder["owner"] = owner
    try:
        yield
    finally:
        _holder["owner"] = None
        _LOCK.release()


def current_owner() -> str | None:
    """Who holds the motion lock right now (None if free) — for diagnostics."""
    return _holder["owner"]
