"""The cognitive layer — recall, deliberate, learn.

``LocalBackend`` is fully self-contained (SQLite memory + a reasoner) and runs
offline. ``HostedBackend`` talks to a hosted cognitive kernel over MCP. Both
satisfy the same ``CognitiveBackend`` interface, so one flag swaps them.
"""

from __future__ import annotations

from .backend import CognitiveBackend
from .local import LocalBackend


def build_cognition(kind: str = "local", **kwargs) -> CognitiveBackend:
    """Construct a cognitive backend by name: ``"local"`` or ``"hosted"``."""
    kind = (kind or "local").lower()
    if kind == "local":
        return LocalBackend(**kwargs)
    if kind == "hosted":
        from .hosted import HostedBackend  # lazy: needs the MCP client + config

        return HostedBackend(**kwargs)
    raise ValueError(f"unknown cognitive backend {kind!r} (expected 'local' or 'hosted')")


__all__ = ["CognitiveBackend", "LocalBackend", "build_cognition"]
