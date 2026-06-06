"""``HostedBackend`` — cognition backed by a hosted kernel over MCP.

This is the "production" path: durable memory, decision rationale, and learned
skills live in a hosted cognitive kernel that the robot (one of many possible
bodies) operates as an MCP client. The mapping is:

    recall(signature)            -> memory_search
    deliberate(observation, goal)-> reasoning model + write_rationale
    learn(signature, decision)   -> memory_learn + register_muscle_memory

It is intentionally a thin, lazily-wired stub: configure the endpoint/key via
``CYGNUS_HOSTED_MCP_URL`` / ``CYGNUS_HOSTED_API_KEY`` to enable it. Until the
session wiring is filled in, calls raise a clear, actionable error rather than
failing silently — the demo and tests use ``LocalBackend``.
"""

from __future__ import annotations

import os
from typing import Optional

from ..types import Corrective, Decision, Observation


class HostedBackend:
    name = "hosted"

    def __init__(self, mcp_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.mcp_url = mcp_url or os.getenv("CYGNUS_HOSTED_MCP_URL")
        self.api_key = api_key or os.getenv("CYGNUS_HOSTED_API_KEY")
        if not self.mcp_url or not self.api_key:
            raise RuntimeError(
                "HostedBackend needs CYGNUS_HOSTED_MCP_URL and CYGNUS_HOSTED_API_KEY. "
                "Use the 'local' backend for offline runs."
            )
        # TODO: open the MCP client session here (mcp.client) and keep it warm.

    def recall(self, signature: str) -> Optional[Corrective]:
        # TODO: call the hosted `memory_search` tool keyed by `signature`.
        raise NotImplementedError("HostedBackend.recall: wire up memory_search over MCP")

    def deliberate(self, observation: Observation, goal: str) -> Decision:
        # TODO: reasoning model call + `write_rationale` over MCP.
        raise NotImplementedError("HostedBackend.deliberate: wire up the reasoning + rationale path")

    def learn(self, signature: str, decision: Decision, outcome: str) -> None:
        # TODO: `memory_learn` + `register_muscle_memory` over MCP.
        raise NotImplementedError("HostedBackend.learn: wire up memory_learn over MCP")
