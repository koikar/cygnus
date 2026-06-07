"""Live MCP validation client for the ReflexOS robot server.

Connects to a running ``reflexos.server --transport http`` and exercises the tools.
Read-only tools (``get_capabilities``, ``get_state``, ``look``) always run; the
``look`` image is saved under ``outputs/``. Movement tools (``home``, ``grip``)
run ONLY when passed explicitly via ``--move`` — so a cluttered workspace can
never trigger an unexpected swing.

    # terminal 1 (camera-authorized, e.g. the Codex terminal): start the server
    python -m reflexos.server --backend so101 --port /dev/tty.usbmodem5A7C1215751 \
        --id reflexos_follower --camera-index 0 \
        --transport http --host 0.0.0.0 --http-port 8000

    # terminal 2: validate (read-only)
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp

    # then, only with a clear workspace, exercise movement:
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp --move home
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp --move grip:open --move grip:close
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp \
        --expect-skill home \
        --move skill:home
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

READ_ONLY = ("get_capabilities", "get_state", "get_robot_model", "list_skills", "audit_skills", "look")


def _dump(result) -> tuple[list[Any], bool]:
    payloads: list[Any] = []
    label = "frame"
    for block in result.content:
        kind = getattr(block, "type", None)
        if kind == "text":
            print(f"  text: {block.text[:400]}")
            try:
                payloads.append(json.loads(block.text))
            except json.JSONDecodeError:
                pass
            if block.text.startswith("camera:"):
                label = block.text.split(":", 1)[1].strip()  # name the next image
        elif kind == "image":
            data = base64.b64decode(block.data)
            Path("outputs").mkdir(exist_ok=True)
            out = Path(f"outputs/look_{label}.png")
            out.write_bytes(data)
            print(f"  image[{label}]: {len(data)} bytes  ->  {out}")
    structured = getattr(result, "structuredContent", None)
    if structured:
        print(f"  structured: {json.dumps(structured)[:400]}")
        payloads.append(structured)
    is_error = bool(getattr(result, "isError", False))
    if is_error:
        print("  >>> tool reported an error")
    return payloads, is_error


def _move_call(spec: str) -> tuple[str, dict]:
    tool, _, arg = spec.partition(":")
    if tool == "grip":
        return "grip", {"mode": arg}
    if tool == "skill":
        return "run_skill", {"name": arg}
    if arg:
        raise ValueError(f"{spec!r} has an argument but {tool!r} does not accept smoke shorthand")
    return tool, {}


async def run(
    url: str,
    moves: list[str],
    *,
    require_tools: list[str],
    expect_skills: list[str],
    allow_tool_errors: bool,
) -> None:
    tool_errors: list[str] = []
    failures: list[str] = []
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print("tools advertised:", tool_names)
            missing_tools = sorted(set(require_tools) - set(tool_names))
            if missing_tools:
                failures.append(f"missing required MCP tools: {missing_tools}")

            seen_skills: set[str] = set()
            for name in READ_ONLY:
                if name not in tool_names:
                    continue
                print(f"\n=== {name} ===")
                payloads, is_error = _dump(await session.call_tool(name, {}))
                if is_error:
                    tool_errors.append(name)
                if name == "list_skills":
                    for payload in payloads:
                        if isinstance(payload, dict) and "name" in payload:
                            seen_skills.add(str(payload["name"]))
                if name == "audit_skills":
                    for payload in payloads:
                        if isinstance(payload, dict) and payload.get("ok") is False:
                            failures.append(f"skill audit failed: {payload}")

            missing_skills = sorted(set(expect_skills) - seen_skills)
            if missing_skills:
                failures.append(f"missing expected skills: {missing_skills}")

            for mv in moves:
                tool, args = _move_call(mv)
                print(f"\n=== MOVE: {tool} {args or ''} ===")
                _, is_error = _dump(await session.call_tool(tool, args))
                if is_error:
                    tool_errors.append(tool)

    print("\n>>> MCP validation complete.")
    if tool_errors and not allow_tool_errors:
        failures.append(f"MCP tool errors: {tool_errors}")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    ap = argparse.ArgumentParser(description="ReflexOS robot MCP smoke test")
    ap.add_argument("--url", default="http://localhost:8000/mcp")
    ap.add_argument(
        "--move",
        action="append",
        default=[],
        metavar="TOOL[:ARG]",
        help="movement tool to run, e.g. 'home', 'grip:open', or "
        "'skill:home' (repeatable). Omit for read-only.",
    )
    ap.add_argument(
        "--require-tool",
        action="append",
        default=[],
        help="fail if this MCP tool is not advertised (repeatable)",
    )
    ap.add_argument(
        "--expect-skill",
        action="append",
        default=[],
        help="fail if this saved skill is not listed by list_skills (repeatable)",
    )
    ap.add_argument(
        "--allow-tool-errors",
        action="store_true",
        help="do not fail the process when a tool returns an MCP error",
    )
    args = ap.parse_args()
    asyncio.run(
        run(
            args.url,
            args.move,
            require_tools=args.require_tool,
            expect_skills=args.expect_skill,
            allow_tool_errors=args.allow_tool_errors,
        )
    )


if __name__ == "__main__":
    main()
