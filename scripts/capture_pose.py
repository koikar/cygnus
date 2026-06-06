"""Kinesthetic pose capture via the LOCAL MCP server (bypasses the cloudflared tunnel).

The tunnel flaps; we're on the same machine as the arm, so talk to localhost.

Usage:
  python scripts/capture_pose.py relax-off              # limp the arm to hand-pose it
  python scripts/capture_pose.py relax-on               # re-lock (hold position)
  python scripts/capture_pose.py capture <skill_name>   # lock + read joints + screenshot + save_skill
  python scripts/capture_pose.py state                  # print current joints (read-only)
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://127.0.0.1:8000/mcp"
OUT = Path("outputs/poses")


def _payloads(result):
    out = []
    label = "frame"
    for block in result.content:
        kind = getattr(block, "type", None)
        if kind == "text":
            try:
                out.append(("json", json.loads(block.text)))
            except json.JSONDecodeError:
                out.append(("text", block.text))
                if block.text.startswith("camera:"):
                    label = block.text.split(":", 1)[1].strip()
        elif kind == "image":
            out.append(("image", (label, base64.b64decode(block.data))))
    return out


def _first_json(payloads):
    for kind, v in payloads:
        if kind == "json":
            return v
    return {}


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    name = sys.argv[2] if len(sys.argv) > 2 else None
    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()

            if cmd == "relax-off":
                _first_json(_payloads(await s.call_tool("relax", {"enabled": False})))
                print("ARM LIMP — hand-pose the claw, then run: capture <name>")
                return
            if cmd == "relax-on":
                await s.call_tool("relax", {"enabled": True})
                print("ARM LOCKED")
                return
            if cmd == "state":
                st = _first_json(_payloads(await s.call_tool("get_state", {})))
                print(json.dumps(st.get("joints", {}), indent=2))
                return
            if cmd == "capture":
                assert name, "capture needs a skill name"
                await s.call_tool("relax", {"enabled": True})  # lock so the pose holds
                joints = _first_json(_payloads(await s.call_tool("get_state", {})))["joints"]
                # screenshot both cameras
                OUT.mkdir(parents=True, exist_ok=True)
                for kind, v in _payloads(await s.call_tool("look", {"camera": "both"})):
                    if kind == "image":
                        cam, data = v
                        (OUT / f"{name}_{cam}.jpg").write_bytes(data)
                steps = [{"tool": "move_to", "args": {"target": joints}}]
                saved = _first_json(
                    _payloads(
                        await s.call_tool(
                            "save_skill",
                            {
                                "name": name,
                                "steps": steps,
                                "description": f"Go to taught position '{name}'.",
                                "notes": "Captured by kinesthetic teaching (relax → hand-pose → lock).",
                            },
                        )
                    )
                )
                print("joints:", json.dumps({k: round(v, 1) for k, v in joints.items()}))
                print("saved:", json.dumps(saved))
                print(f"screenshots: {OUT}/{name}_wrist.jpg , {OUT}/{name}_scene.jpg")
                return
            print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
