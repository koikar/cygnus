"""Live MCP validation client for the Cygnus robot server.

Connects to a running ``cygnus.server --transport http`` and exercises the tools.
Read-only tools (``get_capabilities``, ``get_state``, ``look``) always run; the
``look`` image is saved under ``outputs/``. Movement tools (``home``, ``grip``)
run ONLY when passed explicitly via ``--move`` — so a cluttered workspace can
never trigger an unexpected swing.

    # terminal 1 (camera-authorized, e.g. the Codex terminal): start the server
    python -m cygnus.server --backend so101 --port /dev/tty.usbmodem5A7C1215751 \
        --id cygnus_follower --camera-index 0 \
        --transport http --host 0.0.0.0 --http-port 8000

    # terminal 2: validate (read-only)
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp

    # then, only with a clear workspace, exercise movement:
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp --move home
    python scripts/smoke_mcp.py --url http://localhost:8000/mcp --move grip:open --move grip:close
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

READ_ONLY = ("get_capabilities", "get_state", "look")


def _dump(result) -> None:
    for block in result.content:
        kind = getattr(block, "type", None)
        if kind == "text":
            print(f"  text: {block.text[:400]}")
        elif kind == "image":
            data = base64.b64decode(block.data)
            Path("outputs").mkdir(exist_ok=True)
            out = Path("outputs/look_mcp.png")
            out.write_bytes(data)
            print(f"  image: {len(data)} bytes  ->  {out}")
    structured = getattr(result, "structuredContent", None)
    if structured:
        print(f"  structured: {json.dumps(structured)[:400]}")
    if getattr(result, "isError", False):
        print("  >>> tool reported an error")


async def run(url: str, moves: list[str]) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools advertised:", [t.name for t in tools.tools])

            for name in READ_ONLY:
                print(f"\n=== {name} ===")
                _dump(await session.call_tool(name, {}))

            for mv in moves:
                tool, _, arg = mv.partition(":")
                args = {"mode": arg} if arg else {}
                print(f"\n=== MOVE: {tool} {args or ''} ===")
                _dump(await session.call_tool(tool, args))

    print("\n>>> MCP validation complete.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Cygnus robot MCP smoke test")
    ap.add_argument("--url", default="http://localhost:8000/mcp")
    ap.add_argument(
        "--move",
        action="append",
        default=[],
        metavar="TOOL[:ARG]",
        help="movement tool to run, e.g. 'home' or 'grip:open' (repeatable). "
        "Omit entirely for a read-only run.",
    )
    args = ap.parse_args()
    asyncio.run(run(args.url, args.move))


if __name__ == "__main__":
    main()
