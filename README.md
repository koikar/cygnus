# Cygnus 🦢

**An antifragile control layer for robot arms — robots that get *stronger* from rare failures.**

Built for the **EuroTech × Hong Kong Talent Engage Hackathon** (Munich, June 2026) · **AI & Robotics** track.

---

## The idea

Most autonomous robots are *fragile*: they run beautifully on the happy path and
fail catastrophically the first time reality hands them something they've never
seen — an object in an unexpected spot, a missed grasp, a stalled joint. Those
rare, high-impact, unforeseen events are **black swans**.

Cygnus makes a robot arm **antifragile** — it doesn't just survive black swans,
it gets *better* from them:

1. **System 1 (fast reflex):** routine motions run instantly as validated,
   previously-learned action sequences. No reasoning, no latency.
2. **Black-swan detector:** watches the arm's state and camera — empty gripper
   after a close, a stalled joint, an object where nothing should be, low
   confidence. A *rare failure* fires.
3. **System 2 (deliberation):** a reasoning model looks at the scene, figures out
   a recovery, and — crucially — **records *why*** it did what it did.
4. **Compounding:** the validated recovery is stored as reusable memory. The
   **next** time that swan appears, it's handled instantly as a System-1 reflex.

The demo metric is the **antifragility curve**: recovery time and repeat-failure
rate fall over episodes. The robot literally improves from disorder.

> This dual-process loop (fast reflex ↔ slow deliberation, with a learning bridge
> between them) is inspired by how humans reserve scarce deliberate attention for
> novelty and risk while running everything else on habit.

---

## Architecture — the arm is an MCP server

Cygnus turns the robot arm into a **[Model Context Protocol](https://modelcontextprotocol.io)
(MCP) server**: its body is exposed as tools (`look`, `move_to`, `grip`,
`get_state`, `home`). Any MCP-speaking agent can then *operate* the arm the same
way it would use any other tool — and reason, recover, and learn through a
**pluggable cognitive backend**.

```
   SO-101 arm  ──Python (LeRobot)──►  ROBOT MCP SERVER  (this repo)
   joints + camera                    tools: look · move_to · grip · get_state · home
                                                │
                                                │  MCP
                                                ▼
                          AGENT  +  COGNITIVE BACKEND
                          • reasoning model (System 2) — reasons over the camera frame
                          • memory / rationale — recall fixes, record why, learn
```

**Two backends behind one interface** (`CognitiveBackend`):

- **`LocalBackend`** — fully self-contained (local store + a reasoning model).
  Runs offline, no external account. The repo stands on its own.
- **`HostedBackend`** — connects to a hosted cognitive kernel over MCP
  (durable memory, decision rationale, learned skills) for the "production" path.

Swapping backends is one flag — which is also the antifragile insurance: a flaky
venue network can never freeze the arm, because System 1 and the local backend
keep working.

### One rule: the dual-process boundary is the latency boundary

The reasoning model and any network call are **never** in the high-frequency
motion loop. Routine motion is local and fast; only **escalations and learning
writes** are allowed to be slow.

---

## Hardware

- **[SO-101](https://github.com/TheRobotStudio/SO-ARM100)** open-source arm
  (leader + follower pair), driven by **[Hugging Face LeRobot](https://github.com/huggingface/lerobot)**.
- A **USB-C OpenCV/UVC camera** for vision (`look`). The camera is a separate
  USB device from the Feetech motion bus; Cygnus unifies both behind one MCP
  server. *(Note: Intel RealSense is not supported on macOS — Cygnus uses
  OpenCV/USB cameras and needs no dataset recording for the core demo, so it
  runs on a Mac.)*
- **⚠️ Power:** Leader = **5V**, Follower = **12V**. Wrong voltage permanently
  damages the servos — always verify before powering on.

No model training is required for the core demo: the reasoning model drives the
arm via the MCP tools, and System-1 "reflexes" are recalled tool-call sequences.
(Training a fast policy like ACT/SmolVLA is an optional upgrade for smoother
motion.)

---

## Quickstart

```bash
# Python 3.12 via uv (PyTorch has no 3.13/3.14 wheels yet)
uv venv --python 3.12 && source .venv/bin/activate
uv pip install 'lerobot[feetech]' mcp openai

# brew install ffmpeg   # macOS, if not already present

# Try the whole antifragility loop in simulation — no hardware, no API key:
python -m cygnus demo
```

See **[PLAN.md](./PLAN.md)** for the full build plan and phases.

---

## Running the robot

The robot's body is exposed as an **MCP server** (`cygnus.server`) with five body
tools — `look`, `get_state`, `move_to`, `grip`, `home` — plus the read-only
`get_capabilities` discovery helper. A reasoning agent (Codex, Claude, or a
hosted tedi) connects over MCP and operates the arm. Safety limits are enforced
on every `move_to` regardless of the caller, and actuation tools are annotated
as physical-world/destructive actions so compatible clients can gate them.

| Tool | Channel | Purpose |
| --- | --- | --- |
| `get_capabilities` | MCP only | Discover tool contract, backend, and safety policy. |
| `look` | camera USB-C | Return the camera image plus current state metadata. |
| `get_state` | motion USB-C | Return joint positions and structured scene state. |
| `move_to` | motion USB-C | Move toward joint-space targets, clamped to safe limits. |
| `grip` | motion USB-C | Open or close the gripper. |
| `home` | motion USB-C | Return the arm to the neutral safe pose. |

### 1. Connect and calibrate the arm (once per session)

> **⚠️ Power:** Leader = **5V**, Follower = **12V**. Wrong voltage destroys
> servos — verify before powering on. `Ctrl+C` is the e-stop.

**You only need the follower** (the executor — the arm with the gripper). The
leader is a hand-puppet for teleoperation and for recording ACT/SmolVLA training
demos; Cygnus drives the follower directly via the MCP tools and trains nothing,
so the leader is unused. One arm, one 12V supply, one USB-C — no 5V/12V mix-up.

Validate the two USB devices separately first:

```bash
lerobot-find-port      # motion board: plug in USB-C + 12V power → note the follower port
lerobot-find-cameras opencv   # camera: enumerate OpenCV devices → note the robot camera index
lerobot-calibrate --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=cygnus_follower
```

The camera is already connected by USB-C; `look` uses the OpenCV index selected
with `--camera-index`. On a Mac the built-in FaceTime camera is usually index
`0`, so the robot camera is often `1`+. If OpenCV cannot access the camera,
grant camera permission to the terminal app running the server and retry
`lerobot-find-cameras opencv`.

### 2. Run the robot MCP server

**Pick the transport by where the controlling agent runs:**

```bash
# (a) Agent runs on THIS laptop → stdio (the client spawns the server):
python -m cygnus.server --backend so101 --port <FOLLOWER_PORT> --id cygnus_follower \
    --camera-index <ROBOT_CAMERA_INDEX> --transport stdio

# (b) A REMOTE agent must reach the arm (e.g. a hosted brain) → streamable HTTP:
python -m cygnus.server --backend so101 --port <FOLLOWER_PORT> --id cygnus_follower \
    --camera-index <ROBOT_CAMERA_INDEX> --transport http --host 0.0.0.0 --http-port 8000
```

For the HTTP path, expose the laptop's port and register the public URL with your
agent as an MCP server:

```bash
cloudflared tunnel --url http://localhost:8000      # → https://<id>.trycloudflare.com
# then add  https://<id>.trycloudflare.com/mcp  as an MCP server to your agent
```

No hardware yet? Swap `--backend so101 --port ...` for `--backend sim` — the same
tools run against the simulator. On real hardware, `look` returns the **camera
image** (for the agent's vision model) plus joint/scene state; in sim it returns
the structured scene only. The motion bus can still be debugged independently
from camera enumeration, because they are separate USB devices.

> **Tip — long commands:** end each line with `\` (backslash) so a wrapped paste
> stays one command, e.g. `lerobot-calibrate \` then `  --robot.type=... \` etc.

### Troubleshooting: `Missing motor IDs` / `found motor list: {}`

The control board enumerated over USB (LeRobot connected fine), but **no servos
answered the bus**. This is almost always power or cabling, not software:

1. **Wrong voltage / no servo power.** USB-C powers the board's chip, *not* the
   servos — the board enumerates over USB even with no (or wrong) servo power. If
   the **5V** leader supply is plugged into the **12V** follower, the board lights
   up but the servos can't run. Confirm the **12V** supply, fully seated, and look
   for an **LED on the servos themselves** (no servo LED = no power reaching them).
2. **Loose servo-chain cable.** Reseat the 3-pin cable from board→first servo and
   between each servo; one loose link reports the whole chain empty.
3. **Board channel jumper** on the wrong setting — set it to the USB channel.
4. **USB cable came loose.** Re-check the device still exists:
   `ls /dev/cu.usbmodem* /dev/tty.usbmodem*`. A charge-only USB-C cable powers the
   board but carries no data — use a known data cable.

**Settle software-vs-hardware deterministically** with a non-interactive baud
sweep (no arm movement needed):

```python
from lerobot.motors.feetech.feetech import FeetechMotorsBus
print(FeetechMotorsBus.scan_port("/dev/tty.usbmodemXXXX"))  # {baud: [motor_ids]}
```

If *any* baud lists motor IDs → it's a config/baud issue. If **all** bauds return
empty, the bus is silent → it's power or the servo-chain cable, not software. Fix
the physical setup, then re-run the calibrate command.

### Why Python (when the cognitive layer may be TypeScript)?

Because **the SO-101's entire driver stack — LeRobot — is Python-only.** Talking
to the Feetech bus servos, calibration, and camera capture all go through
LeRobot's `SO101Follower`; there is no Node/TypeScript equivalent. So the process
that *physically touches the arm* must be Python.

That's not a constraint on anything else: **MCP is language-agnostic** (JSON-RPC
over stdio/HTTP). A Python robot server and a TypeScript brain interoperate
cleanly — bridging exactly this kind of language gap is what MCP is *for*. The
arm is Python because the hardware demands it; everything above the MCP boundary
can be whatever language it already is.

---

## Status

🚧 Active build. Verified on macOS (Apple Silicon, Python 3.12) with LeRobot
0.5.1, the MCP SDK, and the OpenAI SDK.

**Working now:**
- Robot **MCP server** (`cygnus.server`) — `get_capabilities`/`look`/`get_state`/
  `move_to`/`grip`/`home`, over **stdio or streamable HTTP**; HTTP endpoint boots
  and serves.
- `SimBackend ⇄ SO101Backend` (one flag) + immutable safety guardrails.
- Self-contained `LocalBackend` cognition + the **antifragility loop** end-to-end
  in sim (`python -m cygnus demo`), with a passing test suite proving novel
  failures escalate once then become fast reflexes.

**Next:** point the server at the real arm at the venue; wire the hosted (tedi)
cognitive path; antifragility dashboard.

## License

[MIT](./LICENSE)
