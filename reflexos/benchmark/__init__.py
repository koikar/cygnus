"""ReflexOS simulated pick-and-place benchmark.

A resettable, seeded, ground-truth-scored simulation of the reflexos
pick-and-place world — the virtual training field a tedi can be put to the test
in over MCP, with none of the hardware (no arm, no 12V, no tunnel).

See ``docs/BENCHMARK.md`` (tedix) for the architecture and how episodes feed the
brain/skills/harness flywheel.
"""

from .pickplace import EnvConfig, PickPlaceEnv

__all__ = ["PickPlaceEnv", "EnvConfig"]
