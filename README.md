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
- A **USB webcam** for vision (`look`). *(Note: Intel RealSense is not supported on
  macOS — Cygnus uses OpenCV/USB cameras and needs no dataset recording for the
  core demo, so it runs on a Mac.)*
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

# Connect the arm (mind the voltages!)
lerobot-find-port                      # identify follower + leader serial ports
lerobot-calibrate --robot.type=so101_follower --robot.port=<PORT> --robot.id=cygnus_follower
lerobot-find-cameras opencv            # find your USB webcam index

# Run Cygnus in simulation (no hardware needed) — coming in this repo:
#   python -m cygnus.server --backend sim
```

See **[PLAN.md](./PLAN.md)** for the full build plan and phases.

---

## Status

🚧 Early build. Environment verified on macOS (Apple Silicon, Python 3.12) with
LeRobot 0.5.1, the MCP SDK, and the OpenAI SDK. Next: the robot MCP server with a
simulator backend, then the agent loop and the antifragility dashboard.

## License

[MIT](./LICENSE)
