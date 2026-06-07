"""MCP server for the pick-and-place benchmark.

Exposes the BENCHMARK.md contract — ``reset / observe / act / score`` — so a tedi
drives the simulated arm over MCP exactly as it drove the physical reflexos arm,
but with seeded resets and ground-truth scoring it can learn against.

  python -m reflexos.benchmark serve                      # stdio (local agent)
  python -m reflexos.benchmark serve --transport http --http-port 8010
"""

from __future__ import annotations

import argparse

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .pickplace import EnvConfig, PickPlaceEnv

mcp = FastMCP("reflexos-benchmark")

_READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
_ACTUATE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

_env = PickPlaceEnv()


@mcp.tool(annotations=_ACTUATE)
def reset_episode(seed: int | None = None, cube_position: int | None = None, target_bucket: str | None = None) -> dict:
    """Start a fresh episode. Pass ``seed`` for a reproducible random task, or an
    explicit ``cube_position`` (1-6) + ``target_bucket`` (left/right/front)."""
    task = None
    if cube_position is not None and target_bucket is not None:
        task = {"cube_position": cube_position, "target_bucket": target_bucket}
    return _env.reset(seed=seed, task=task)


@mcp.tool(annotations=_READ_ONLY)
def get_observation() -> dict:
    """Perceive the scene: end-effector location, gripper, holding, cube location, target bucket."""
    return _env.observe()


@mcp.tool(annotations=_ACTUATE)
def move_to(target: str) -> dict:
    """Move the arm to ``home``, ``pos:N`` (1-6), or ``bucket:left|right|front``.
    Route through ``home`` between stops or it is logged as a policy violation."""
    return _env.move_to(target)


@mcp.tool(annotations=_ACTUATE)
def set_gripper(state: str) -> dict:
    """``closed`` grasps the cube only if aligned with its position; ``open`` over
    the target bucket delivers it (anywhere else drops it)."""
    return _env.set_gripper(state)


@mcp.tool(annotations=_ACTUATE)
def home() -> dict:
    """Convenience: move to ``home``."""
    return _env.home()


@mcp.tool(annotations=_READ_ONLY)
def score_episode() -> dict:
    """Ground-truth verdict: success = cube delivered to the target bucket, plus
    steps and policy violations."""
    return _env.score()


def main() -> None:
    parser = argparse.ArgumentParser(description="ReflexOS pick-and-place benchmark MCP server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=8010)
    parser.add_argument("--grasp-reliability", type=float, default=1.0)
    parser.add_argument("--no-home-policy", action="store_true", help="disable the route-through-home policy check")
    args = parser.parse_args()

    global _env
    _env = PickPlaceEnv(EnvConfig(grasp_reliability=args.grasp_reliability, require_home_between=not args.no_home_policy))

    if args.transport == "stdio":
        mcp.run("stdio")
    else:
        mcp.settings.host = args.host
        mcp.settings.port = args.http_port
        mcp.run("streamable-http" if args.transport == "http" else "sse")


if __name__ == "__main__":
    main()
