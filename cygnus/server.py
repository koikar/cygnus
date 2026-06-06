"""The robot MCP server — the arm's body exposed as MCP tools.

Any MCP-speaking agent (or a hosted cognitive kernel / tedi) can operate the arm
through ``look`` / ``get_state`` / ``move_to`` / ``grip`` / ``home``. The active
body is chosen by ``--backend sim|so101``; safety guardrails are enforced on
every ``move_to`` regardless of caller.

Transport (``--transport``):
  * ``stdio`` — the MCP client spawns this as a local subprocess. Use when the
    agent runs on the SAME machine the arm is plugged into.
  * ``http``  — streamable HTTP server on ``--host:--port``. Use when a remote
    agent (e.g. a hosted tedi) must reach the arm over the network; expose it
    with a tunnel (cloudflared/ngrok) and add that URL to the tedi.

    # local agent on this laptop:
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodemXXXX --transport stdio
    # reachable by a remote tedi:
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --transport http --host 0.0.0.0 --http-port 8000
"""

from __future__ import annotations

import argparse
import json

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ToolAnnotations

from .robot import build_backend
from .robot.base import RobotBackend
from .safety import clamp_action
from .types import Observation

mcp = FastMCP("cygnus-robot")

# MCP annotations are read by the consuming platform (e.g. a tedi's catalog scan)
# to drive approval UX: read-only perception needs no gate; actuation acts on the
# physical world. Flip `destructive` to True on the actuators to force per-move
# human approval; the immutable guardrails in `safety.py` apply either way.
_READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
_ACTUATE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)

# Set by main(); the tools operate this body.
_robot: RobotBackend | None = None


def _backend() -> RobotBackend:
    if _robot is None:
        raise RuntimeError("robot backend not initialized; run via `python -m cygnus.server`")
    return _robot


def _obs_to_dict(obs: Observation) -> dict:
    """MCP-serializable view of an observation (the raw frame is omitted)."""
    return {
        "joints": obs.joints,
        "scene": obs.scene,
        "grasped": obs.grasped,
        "has_frame": obs.frame is not None,
        "note": obs.note,
    }


@mcp.tool(annotations=_READ_ONLY)
def get_state() -> dict:
    """Return current joint positions and the structured scene."""
    return _obs_to_dict(_backend().get_observation())


def _encode_jpeg(frame) -> bytes | None:
    """Encode an OpenCV/ndarray frame to JPEG bytes; None if it can't be encoded."""
    try:
        import cv2

        ok, buf = cv2.imencode(".jpg", frame)
        return buf.tobytes() if ok else None
    except Exception:
        return None


@mcp.tool(annotations=_READ_ONLY)
def look():
    """Capture the current scene. On real hardware this returns the camera image
    (for the agent's vision model) alongside the joint/scene state; in simulation
    it returns the structured scene only."""
    obs = _backend().look()
    state = _obs_to_dict(obs)
    if obs.frame is not None:
        jpeg = _encode_jpeg(obs.frame)
        if jpeg is not None:
            # Image first so the agent perceives it; state as a JSON text block.
            return [Image(data=jpeg, format="jpeg"), json.dumps(state)]
    return state


@mcp.tool(annotations=_ACTUATE)
def move_to(target: dict[str, float]) -> dict:
    """Move toward a joint-space target. Keys are '<joint>.pos'. Clamped to safe limits."""
    return _obs_to_dict(_backend().move_to(clamp_action(target)))


@mcp.tool(annotations=_ACTUATE)
def grip(mode: str) -> dict:
    """Open or close the gripper. ``mode`` is 'open' or 'close'."""
    return _obs_to_dict(_backend().grip(mode))


@mcp.tool(annotations=_ACTUATE)
def home() -> dict:
    """Return the arm to its safe neutral pose."""
    return _obs_to_dict(_backend().home())


def main() -> None:
    parser = argparse.ArgumentParser(description="Cygnus robot MCP server")
    parser.add_argument("--backend", default="sim", choices=["sim", "so101"])
    parser.add_argument("--port", help="serial port for the SO-101 (so101 backend)")
    parser.add_argument("--id", default="cygnus_follower", help="calibration id (so101 backend)")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="stdio (local subprocess) or http (network, for a remote tedi)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host for http/sse")
    parser.add_argument("--http-port", type=int, default=8000, help="bind port for http/sse")
    args = parser.parse_args()

    global _robot
    if args.backend == "so101":
        if not args.port:
            parser.error("--port is required for the so101 backend (see `lerobot-find-port`)")
        _robot = build_backend(
            "so101", port=args.port, id=args.id, camera_index=args.camera_index
        )
    else:
        _robot = build_backend("sim")
    _robot.connect()

    if args.transport == "stdio":
        mcp.run("stdio")
    else:
        # streamable-http / sse: bind a network listener a remote tedi can reach.
        mcp.settings.host = args.host
        mcp.settings.port = args.http_port
        mcp.run("streamable-http" if args.transport == "http" else "sse")


if __name__ == "__main__":
    main()
