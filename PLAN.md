# Cygnus — Build Plan

Hackathon build plan for an **antifragile control layer for the SO-101 robot arm**,
exposed as an MCP server and driven by a reasoning model with a learning loop.
See [README.md](./README.md) for the concept.

---

## Architecture recap

```
   SO-101 arm  ──Python (LeRobot)──►  ROBOT MCP SERVER  (this repo)
   motion USB-C + camera USB-C         tools: get_capabilities · look · move_to · grip · get_state · home
                                                │  MCP
                                                ▼
                          AGENT (System 2 reasoning)  +  COGNITIVE BACKEND
                                       LocalBackend  ⇄  HostedBackend (one flag)
```

**Model split — do not confuse the two:**

| | Robot policy (ACT / SmolVLA, *optional*) | Reasoning model (System 2) |
| --- | --- | --- |
| Input | camera pixels + joints | text + camera image |
| Output | raw motor vectors | reasoning + **tool calls** |
| Speed | 30+ Hz, local | ~1–2 s/decision, API |
| Reasons / calls tools? | no | **yes** |

Core demo uses **LLM-as-controller** (reasoning model drives the arm via MCP
tools) → **no training required**. System-1 reflexes are recalled, validated
tool-call sequences.

---

## Robot MCP server — tool surface

| Tool | Args | Returns | Notes |
| --- | --- | --- | --- |
| `get_capabilities` | – | tool contract + safety policy | read-only discovery for agents |
| `look` | – | image + brief scene note | reads the USB-C OpenCV/UVC camera frame |
| `get_state` | – | joint positions | `{shoulder_pan.pos, …, gripper.pos}` |
| `move_to` | joint targets | new state | joint-space; clamped to safe limits |
| `grip` | `open`/`close` | new state + grasp guess | |
| `home` | – | new state | safe reset pose |

**Immutable guardrails live in the server** (joint limits, workspace bounds,
e-stop). The learning loop can add reflexes but can never relax a safety
constraint — the anti-"misevolution" boundary. Actuation tools are annotated as
physical-world/destructive MCP calls so Codex, Claude, and tedi can put human
approval in front of motion where supported.

`RobotBackend` interface: `SimBackend` (offline, synthetic frames + state) ⇄
`SO101Backend` (real arm). One flag switches them.

---

## Verified API (LeRobot 0.5.1, macOS arm64 / Python 3.12)

In 0.5.1 the SO-100/SO-101 are unified under `so_follower` (not `so101_follower`):

```python
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

robot = SO101Follower(SO101FollowerConfig(
    port="/dev/tty.usbmodemXXXX",       # from lerobot-find-port
    id="cygnus_follower",                # must match the calibration id
    max_relative_target=None,            # built-in safety clamp (set a cap for guardrails)
    cameras={"front": OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=30)},
))
robot.connect(calibrate=True)            # get_observation() -> {"<joint>.pos": float, ..., "front": ndarray}
robot.send_action({"gripper.pos": 30.0}) # same "<joint>.pos" keys
robot.disconnect()
```

CLI entry points: `lerobot-find-port`, `lerobot-find-cameras`, `lerobot-calibrate`,
`lerobot-teleoperate`, `lerobot-record`, `lerobot-train`. Build the MCP server with
`from mcp.server.fastmcp import FastMCP`.

---

## Phases

### Phase 0 — Laptop only, no hardware
1. venv + install (`lerobot[feetech]`, `mcp`, `openai`, `ffmpeg`). ✅ done
2. Robot MCP server with **`SimBackend`** — fake arm returns synthetic frame +
   state. Full loop runs with zero hardware.
3. Agent loop (reasoning model) wired to the robot MCP server + cognitive backend.
4. End-to-end in sim: goal → recall (miss) → reason → recover → store → re-run →
   recall (hit) → fast replay. **The antifragility loop works before hardware.**

### Phase 1 — Connect the arm (~1–3 hrs, mostly cabling)
> **⚠️ POWER:** Leader **5V**, Follower **12V** — wrong voltage destroys servos.
> Use only the follower for the Cygnus demo. Motor-ID setup is pre-done on
> hackathon arms (skip `lerobot-setup-motors`).
> `Ctrl+C` to e-stop; if joints lock, unplug power, wait, replug. Use one
> consistent `--robot.id` across calibrate + runtime.

```bash
lerobot-find-port           # motion board USB-C
lerobot-find-cameras opencv # camera USB-C
lerobot-calibrate --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=cygnus_follower
```

### Phase 2 — Point the server at the real arm
Flip `SimBackend` → `SO101Backend` (port + id + camera index). Same agent loop
now moves a real arm and sees through the robot camera:

```bash
python -m cygnus.server --backend so101 \
  --port <FOLLOWER_PORT> \
  --id cygnus_follower \
  --camera-index <ROBOT_CAMERA_INDEX> \
  --transport http --host 0.0.0.0 --http-port 8000
```

### Phase 3 — The antifragile demo
1. Goal ("place the cube in the bin") → routine path = System-1 replay.
2. **Inject a black swan** (move the cube somewhere novel / block the gripper).
   Detector fires.
3. Escalate → reasoning model recovers → record rationale + store the corrective.
4. Re-inject → recall the fix → fast System-1 handling. Show the
   **antifragility curve** + rationale timeline on the dashboard.

### Phase 4 — Stretch
- **Fleet:** multiple arms share one cognitive backend → arm 1's lesson is
  recalled by arm N. The shared memory *is* the mesh.
- Trained **ACT** policy for smooth fast System-1 motion (replaces LLM-as-controller
  for routine moves; needs a Linux machine + camera for dataset recording).

---

## Caveats

- LLM-as-controller is **slow/jerky** (per-step API round-trips) — fine for
  deliberate manipulation, not fast motion. That's *why* System-1 replay exists.
- macOS: Intel RealSense unsupported; USB/OpenCV webcams work. Core demo needs no
  dataset recording, so a Mac is fine; the ACT-training stretch needs Linux.
- Power voltages (5V/12V) are the single biggest way to destroy hardware — verify
  every time.
- Confirm the reasoning-model deployment is **vision-capable** (it reasons off the
  camera frame).

---

## References

- LeRobot: https://github.com/huggingface/lerobot · docs: https://huggingface.co/docs/lerobot
- SO-ARM100/101 hardware: https://github.com/TheRobotStudio/SO-ARM100
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- SmolVLA: https://huggingface.co/docs/lerobot/smolvla
