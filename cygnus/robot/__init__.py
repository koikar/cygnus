"""Robot backends — the arm's body, behind one interface.

``SimBackend`` runs the whole stack on a laptop with no hardware; ``SO101Backend``
drives the real arm via LeRobot. One flag switches them (see ``build_backend``).
"""

from __future__ import annotations

from .base import RobotBackend
from .sim import SimBackend


def build_backend(kind: str = "sim", **kwargs) -> RobotBackend:
    """Construct a robot backend by name: ``"sim"`` or ``"so101"``."""
    kind = (kind or "sim").lower()
    if kind == "sim":
        return SimBackend(**kwargs)
    if kind in ("so101", "real"):
        from .so101 import SO101Backend  # lazy: avoids importing LeRobot in sim

        return SO101Backend(**kwargs)
    raise ValueError(f"unknown robot backend {kind!r} (expected 'sim' or 'so101')")


__all__ = ["RobotBackend", "SimBackend", "build_backend"]
