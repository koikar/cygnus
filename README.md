# ReflexOS 🦢

**An antifragile control layer for robot arms — robots that get *stronger* from rare failures.**

Built for the **EuroTech × Hong Kong Talent Engage Hackathon** (Munich, June 2026) · **AI & Robotics** track.

---

## The idea

Most autonomous robots are *fragile*: they run beautifully on the happy path and
fail catastrophically the first time reality hands them something they've never
seen — an object in an unexpected spot, a missed grasp, a stalled joint. Those
rare, high-impact, unforeseen events are **black swans**.

ReflexOS makes a robot arm **antifragile** — it doesn't just survive black swans,
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

ReflexOS turns the robot arm into a **[Model Context Protocol](https://modelcontextprotocol.io)
(MCP) server**: its body is exposed as a surface of **safe primitives** (perceive,
move in joint- or task-space, grip) plus **saved skills** (validated, replayable
tool-call sequences). Any MCP-speaking agent can then *operate* the arm the same
way it would use any other tool — and reason, recover, and learn through a
**pluggable cognitive backend**.

```
   SO-101 arm  ──Python (LeRobot)──►  ROBOT MCP SERVER  (this repo)
   joints + 2 cameras                 perception · joint + Cartesian (FK/IK) · gripper
                                       teaching/skills · safety guardrails
                                                │
                                                │  MCP
                                                ▼
                          AGENT  +  COGNITIVE BACKEND
                          • reasoning model (System 2) — reasons over the camera frame
                          • memory / rationale — recall fixes, record why, learn
```

The boundary is deliberate: the LLM **plans** by composing vetted primitives and
recalling skills — it does **not** improvise raw joint vectors into the motor bus.
This is the SayCan / Code-as-Policies pattern: an LLM planner on top of grounded,
safety-clamped skills with perception in the verification loop. Every actuation
is clamped to joint/workspace limits regardless of what the caller asks for.

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
  USB device from the Feetech motion bus; ReflexOS unifies both behind one MCP
  server. *(Note: Intel RealSense is not supported on macOS — ReflexOS uses
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
python -m reflexos demo
```

See **[PLAN.md](./PLAN.md)** for the full build plan and phases.

---

## Running the robot

The robot's body is exposed as an **MCP server** (`reflexos.server`). A reasoning
agent (Codex, Claude, or a hosted tedi) connects over MCP and operates the arm by
composing these primitives and recalling saved skills. Safety limits are enforced
on every motion regardless of the caller, and actuation tools are annotated as
physical-world/destructive actions so compatible clients can gate them.

**Perception** — see the body and the scene:

| Tool | Purpose |
| --- | --- |
| `get_capabilities` | Discover the tool contract, backend, and safety policy (read-only). |
| `get_robot_model` | Agent-facing body schema: joints, limits, presets, current state. |
| `get_state` | Current joint positions + structured scene. |
| `look` | Capture a camera frame — `wrist` (eye-in-hand, default), `scene`, or `both`. |
| `get_joint_effects` | FK finite-difference map: what a +1° on each joint does to the claw (mm/rad). |
| `detect_colored_blocks` | Find colored blocks in a frame; annotated with table targets when calibrated. |

**Cartesian control** — task-space via FK/IK (placo + the bundled SO-101 URDF):

| Tool | Purpose |
| --- | --- |
| `get_ee_pose` | End-effector `(x, y, z)` + orientation from FK. |
| `move_ee_to` | Move to an absolute base-frame point (IK → joints), workspace-checked. |
| `move_ee_by` | Translate the gripper by `(dx, dy, dz)`, capped per step. |

**Joint control** — fine/low-level:

| Tool | Purpose |
| --- | --- |
| `move_to` | Move toward absolute joint targets, clamped to safe limits. |
| `move_relative` | Apply relative joint deltas, clamped. |

**Gripper:**

| Tool | Purpose |
| --- | --- |
| `set_gripper` | Set jaw position (`~15` = closed, `~60` = open; not cm). |
| `grip` | Preset wrapper: `open` / `close`. |

**Teaching & skills** — capture and replay:

| Tool | Purpose |
| --- | --- |
| `relax` | Torque on/off for kinesthetic hand-teaching (limp the arm, pose it, re-lock). |
| `save_skill` | Save an ordered tool-call sequence as `skills/<name>.json` (recording only — no motion). |
| `run_skill` | Replay a saved skill's steps in order (open-loop). |
| `list_skills` / `audit_skills` | List skills; validate them against the current body schema. |
| `run_sequence` | Execute an inline list of tool calls as one guarded sequence. |

**Pose & safety:**

| Tool | Purpose |
| --- | --- |
| `home` | Return to the canonical harness-rest pose (`poses.HOME`), wrist cam facing up. |
| `wait_until_settled` | Poll until the pose stops changing (commands no motion). |
| `set_speed` | Lower servo acceleration/velocity for smooth motion (default Accel `254` is snappy). |
| `fit_table_calibration` / `get_table_calibration` / `project_pixel_to_table` | Pixel→table homography for grounded vision targets. |

**Built-in safety guardrails** (immutable — the learning loop can add reflexes but
never relax a limit):

- **Joint clamp** (`clamp_action`): every joint target is forced into its safe
  range; unknown/typo'd joint keys are dropped, never forwarded to the bus.
- **Workspace bounds + `check_ee_target`**: Cartesian targets must stay inside the
  base-frame box (default `x 0.08–0.46`, `y ±0.28`, `z −0.10–0.38` m); single EE
  steps are capped (`REFLEXOS_MAX_STEP_M`, default `0.05` m).
- **Motion lock**: one process-wide actuation lock serializes motion across
  concurrent clients (Claude + Codex + tedis share one arm) — callers wait, then
  fail closed with `MotionBusy` rather than interleaving motor commands.
- **`set_speed`**: lowers servo acceleration/velocity so moves are smooth.

### The skills library

Skills are saved tool-call sequences under `skills/*.json`, replayable with
`run_skill`. The headline set is **7 taught poses captured by kinesthetic teaching**
(`relax` → hand-pose the claw → `save_skill`, via `scripts/capture_pose.py`):
`paper_pos_1`..`paper_pos_6` (six paper drop/pick positions) and `home` (the single
canonical rest pose). On replay they land within roughly **1°** of the taught
target. Skills are **tagged by `kind`** (position / pick / place / primitive / home
/ perception / demo) and **composable** — `grab_at_N`/`drop_at_N` reference
`paper_pos_N`, so re-teaching a position propagates everywhere. Plus `grab`/`release`
(close/open the jaw) and demo skills (`home_reach_grab_home_demo`, `survey_blocks`).
Early learning-phase probes are archived under `skills/_archive/`.

> The full motion vocabulary — joint directions, the FK/IK layers, calibration,
> and validated grab routes — lives in **[docs/MOTIONS.md](./docs/MOTIONS.md)**.

### 1. Connect and calibrate the arm (once per session)

> **⚠️ Power:** Leader = **5V**, Follower = **12V**. Wrong voltage destroys
> servos — verify before powering on. `Ctrl+C` is the e-stop.

**You only need the follower** (the executor — the arm with the gripper). The
leader is a hand-puppet for teleoperation and for recording ACT/SmolVLA training
demos; ReflexOS drives the follower directly via the MCP tools and trains nothing,
so the leader is unused. One arm, one 12V supply, one USB-C — no 5V/12V mix-up.

Validate the two USB devices separately first:

```bash
lerobot-find-port      # motion board: plug in USB-C + 12V power → note the follower port
lerobot-find-cameras opencv   # camera: enumerate OpenCV devices → note the robot camera index
lerobot-calibrate --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=reflexos_follower
```

The camera is already connected by USB-C; `look` uses the OpenCV index selected
with `--camera-index`. On a Mac the built-in FaceTime camera is usually index
`0`, so the robot camera is often `1`+. If OpenCV cannot access the camera,
grant camera permission to the terminal app running the server and retry
`lerobot-find-cameras opencv`.

### 2. Run the robot MCP server

The simplest path is the bundled launcher, run from a **camera-authorized
terminal** so the wrist camera (index `0`) initializes:

```bash
bash scripts/run_robot.sh
```

It starts `reflexos.server` on the `so101` backend with the wrist camera (index 0)
and an optional scene camera (index 1), serves streamable HTTP on
`127.0.0.1:8000`, pulls the `server` / `robot` / `kinematics` extras (mcp +
lerobot + placo), and mirrors logs to `outputs/server.log`. Override with
`REFLEXOS_PORT`, `REFLEXOS_CAMERA` (`-1` = motion-only), `REFLEXOS_SCENE_CAMERA`,
`REFLEXOS_HTTP_PORT`.

To run it by hand and pick the transport by where the controlling agent runs:

```bash
# (a) Agent runs on THIS laptop → stdio (the client spawns the server):
python -m reflexos.server --backend so101 --port <FOLLOWER_PORT> --id reflexos_follower \
    --camera-index <ROBOT_CAMERA_INDEX> --transport stdio

# (b) A REMOTE agent must reach the arm (e.g. a hosted brain) → streamable HTTP:
python -m reflexos.server --backend so101 --port <FOLLOWER_PORT> --id reflexos_follower \
    --camera-index <ROBOT_CAMERA_INDEX> --transport http --host 0.0.0.0 --http-port 8000
```

For a remote agent you can front the HTTP port with a cloudflared tunnel and
register the public `/mcp` URL as an MCP server. **The tunnel is flaky**, so any
agent running *on the same machine as the arm* should talk to `localhost`
(`http://127.0.0.1:8000/mcp`) directly — that's what `scripts/capture_pose.py`
and `scripts/smoke_mcp.py` do.

### 3. Two local agents sharing one arm (Claude Code + Codex)

The SO-101 serial port has a **single owner** — only one process can hold it.
So when more than one client should drive the arm, run **one** HTTP server (it
owns the serial bus and the camera) and point every client at it. Do **not**
register the arm as a `stdio` server in two clients: each would spawn its own
`reflexos.server`, and they'd collide on the port.

```bash
# 1. ONE server, launched from a camera-authorized terminal so --camera-index 0 works.
#    (If the launching app lacks camera permission, use --camera-index -1 = motion-only.)
python -m reflexos.server --backend so101 --port <FOLLOWER_PORT> --id reflexos_follower \
    --camera-index 0 --transport http --host 127.0.0.1 --http-port 8000

# 2. Register the same URL with each client:
claude mcp add --transport http reflexos-robot http://127.0.0.1:8000/mcp
codex  mcp add reflexos-robot --url http://127.0.0.1:8000/mcp
```

Because the *server* process holds the camera, `look` returns images to **every**
client regardless of that client app's own camera permission. Validate with
`scripts/smoke_mcp.py --url http://127.0.0.1:8000/mcp` (read-only; add `--move
home` only with a clear workspace). To capture a new taught pose, limp the arm and
save it with `scripts/capture_pose.py` (`relax-off` → hand-pose → `capture <name>`).

### Operational learnings (real-arm sessions)

- **12V power is required for the servos.** USB-C only powers the control board's
  chip — the board enumerates over USB even with no servo power. No servo LED / a
  silent bus = power or servo-chain cabling, not software.
- **The wrist camera read-thread can go stale.** The so101 backend falls back to
  joint-only state when a frame stalls, so `get_state` keeps working.
- **The cloudflared tunnel (`reflexos.tedi.studio`) is flaky** — local agents should
  use `localhost`, not the public URL.
- **Servo Acceleration defaults to `254`** (snappy/jerky); `set_speed` lowers it
  for smooth motion.
- **`gripper.pos` is a percentage, not cm**: `~15` = closed, `~60` = open.
- **`poses.HOME` is the single canonical harness-rest pose** — arm-only (no gripper)
  so homing never drops a carried object; the `home` tool and `home` skill share it.
- **The wrist camera is mounted rotated ~90°** — never reason left/right from the
  raw wrist frame; use the scene camera or Cartesian control.

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
- Robot **MCP server** (`reflexos.server`) driving a **real SO-101 follower**, over
  **stdio or streamable HTTP**. Full tool surface: perception
  (`look`/`get_state`/`get_robot_model`/`get_joint_effects`/`detect_colored_blocks`),
  Cartesian FK/IK (`get_ee_pose`/`move_ee_to`/`move_ee_by`, placo + bundled URDF),
  joint control (`move_to`/`move_relative`), gripper (`set_gripper`/`grip`),
  teaching/skills (`relax`/`save_skill`/`run_skill`/`list_skills`/`audit_skills`/
  `run_sequence`), and pose/safety (`home`/`set_speed`/`wait_until_settled`/
  table calibration).
- `SimBackend ⇄ SO101Backend` (one flag) + immutable safety guardrails (joint
  clamp, workspace bounds, motion lock for concurrent clients).
- **Skills library** including 7 kinesthetically-taught poses (`paper_pos_1`..`6`
  + `home`), `grab`/`release`, and demo routines — validated to land within
  ~1° of target on replay.
- Self-contained `LocalBackend` cognition + the **antifragility loop** end-to-end
  in sim (`python -m reflexos demo`), with a passing test suite proving novel
  failures escalate once then become fast reflexes.

**Next:** wire the hosted (tedi) cognitive path end-to-end on the real arm;
antifragility dashboard.

## License

[MIT](./LICENSE)
