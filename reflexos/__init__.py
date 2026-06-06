"""ReflexOS — an antifragile control layer for robot arms.

The robot's body is exposed as an MCP server (``reflexos.server``); a reasoning
agent operates it through a pluggable cognitive backend that *recalls* known
reflexes, *deliberates* on novel failures ("black swans"), and *learns* the
recovery so the next occurrence is handled instantly.

See ``PLAN.md`` for the full architecture and build phases.
"""

__version__ = "0.1.0"
