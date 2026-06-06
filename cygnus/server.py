"""The robot MCP server — the arm's body exposed as MCP tools.

Any MCP-speaking agent (Codex, Claude, or a hosted tedi) can operate the arm
through ``look`` / ``get_state`` / ``move_to`` / ``grip`` / ``home``. The active
body is chosen by ``--backend sim|so101``; safety guardrails are enforced on
every ``move_to`` regardless of caller. On real hardware the body has two USB
channels: Feetech serial for motion, and an OpenCV/UVC camera for vision.

Transport (``--transport``):
  * ``stdio`` — the MCP client spawns this as a local subprocess. Use when the
    agent runs on the SAME machine the arm is plugged into.
  * ``http``  — streamable HTTP server on ``--host:--port``. Use when a remote
    agent (e.g. a hosted tedi) must reach the arm over the network; expose it
    with a tunnel (cloudflared/ngrok) and add that URL to the tedi.

    # local agent on this laptop:
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --camera-index 1 --transport stdio
    # reachable by a remote tedi:
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodemXXXX \
        --camera-index 1 --transport http --host 0.0.0.0 --http-port 8000
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
# to drive approval UX: read-only perception needs no gate; actuation moves
# physical hardware and should be gated by the client where supported.
_READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
_ACTUATE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True
)

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
def get_capabilities() -> dict:
    """Return the robot MCP contract and safety envelope."""
    return {
        "name": "cygnus-robot",
        "backend": _backend().name,
        "tools": {
            "look": "Capture the camera image plus current robot state.",
            "get_state": "Return joint positions and structured scene state.",
            "move_to": "Move toward safe joint-space targets; targets are clamped.",
            "grip": "Open or close the gripper.",
            "home": "Return to the neutral safe pose.",
        },
        "hardware_channels": {
            "motion": "SO-101 follower / Feetech serial bus over USB",
            "vision": "OpenCV/UVC camera over USB",
        },
        "safety": {
            "move_to_clamped": True,
            "actuation_tools_destructive": True,
            "e_stop": "Ctrl+C the server or remove robot power.",
        },
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
    if mode not in {"open", "close"}:
        raise ValueError(f"grip mode must be 'open' or 'close', got {mode!r}")
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
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="OpenCV camera index for the so101 backend; use -1 to run motion-only (no camera)",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="stdio (local subprocess) or http (network, for a remote tedi)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host for http/sse")
    parser.add_argument("--http-port", type=int, default=8000, help="bind port for http/sse")
    parser.add_argument(
        "--public-host",
        action="append",
        default=[],
        metavar="HOST",
        help="public hostname this server is reachable at behind a tunnel "
        "(e.g. cygnus.tedi.studio); repeatable. Added to the MCP DNS-rebinding "
        "allow-list so requests arriving with that Host header are accepted.",
    )
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
        # streamable-http / sse: bind a network listener a remote agent can reach.
        mcp.settings.host = args.host
        mcp.settings.port = args.http_port
        if args.public_host:
            # Behind a tunnel (e.g. cloudflared → cygnus.tedi.studio) the request
            # arrives with the public Host header, which DNS-rebinding protection
            # blocks by default. Allow the named hosts while keeping localhost.
            from mcp.server.transport_security import TransportSecuritySettings

            allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
            allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
            for h in args.public_host:
                allowed_hosts += [h, f"{h}:*"]
                allowed_origins += [f"https://{h}", f"http://{h}"]
            mcp.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=True,
                allowed_hosts=allowed_hosts,
                allowed_origins=allowed_origins,
            )
        mcp.run("streamable-http" if args.transport == "http" else "sse")


if __name__ == "__main__":
    main()
