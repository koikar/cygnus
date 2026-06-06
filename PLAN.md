# ReflexOS — Build Plan

Hackathon build plan for an **AI-native training layer for the SO-101 robot arm**,
exposed as an MCP server and driven by a reasoning agent that can teach,
correct, and save robot workflows.
See [README.md](./README.md) for the concept.

---

## Architecture recap

```
   SO-101 arm  ──Python (LeRobot)──►  ROBOT MCP SERVER  (this repo)
   motion USB-C + 2 cameras            perception · joint + Cartesian · gripper · teaching/skills · safety
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

Core demo uses **agent-as-trainer** (reasoning model drives the arm via MCP
tools) → **no leader arm or pre-recorded dataset required** for the first proof.
System-1 reflexes are recalled, validated tool-call sequences learned from
successful attempts.

---

## Robot MCP server — tool surface

The surface grew from the original 6 tools into layered groups. The full,
authoritative list lives in **[README.md](./README.md)**; the layered motion
vocabulary is in **[docs/MOTIONS.md](./docs/MOTIONS.md)**. Summary:

| Group | Tools |
| --- | --- |
| Perception | `get_capabilities` · `get_robot_model` · `get_state` · `look` · `get_joint_effects` · `detect_colored_blocks` |
| Cartesian (FK/IK, placo + URDF) | `get_ee_pose` · `move_ee_to` · `move_ee_by` |
| Joint | `move_to` · `move_relative` |
| Gripper | `set_gripper` · `grip` |
| Teaching / skills | `relax` · `save_skill` · `run_skill` · `list_skills` · `audit_skills` · `run_sequence` |
| Pose / safety / calibration | `home` · `wait_until_settled` · `set_speed` · `fit_table_calibration` · `get_table_calibration` · `project_pixel_to_table` |

**Immutable guardrails live in the server** (joint clamp, Cartesian workspace
bounds + `check_ee_target`, a process-wide motion lock for concurrent clients,
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
    id="reflexos_follower",                # must match the calibration id
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
4. End-to-end in sim: goal → attempt → observe → correct → store → re-run →
   recall (hit) → fast replay. **The agent-training loop works before hardware.**

### Phase 1 — Connect the arm (~1–3 hrs, mostly cabling) ✅ done
> **⚠️ POWER:** Leader **5V**, Follower **12V** — wrong voltage destroys servos.
> Use only the follower for the ReflexOS demo. Motor-ID setup is pre-done on
> hackathon arms (skip `lerobot-setup-motors`).
> `Ctrl+C` to e-stop; if joints lock, unplug power, wait, replug. Use one
> consistent `--robot.id` across calibrate + runtime.

```bash
lerobot-find-port           # motion board USB-C
lerobot-find-cameras opencv # camera USB-C
lerobot-calibrate --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=reflexos_follower
```

### Phase 2 — Point the server at the real arm ✅ done
Flip `SimBackend` → `SO101Backend` (port + id + camera index). Same agent loop
now moves a real arm and sees through the robot camera. Use the bundled launcher
`bash scripts/run_robot.sh` (so101 backend, wrist cam 0 + scene cam 1, HTTP on
`127.0.0.1:8000`), or by hand:

```bash
python -m reflexos.server --backend so101 \
  --port <FOLLOWER_PORT> \
  --id reflexos_follower \
  --camera-index <ROBOT_CAMERA_INDEX> \
  --transport http --host 0.0.0.0 --http-port 8000
```

### Phase 3 — The AI-native training demo
1. Give the robot a new workflow ("place the cube in the bin") with no
   pre-recorded leader-arm demonstration.
2. The agent uses MCP tools to inspect the robot model, observe the scene, choose
   safe motions, and attempt the workflow.
3. When the attempt fails or the environment changes, the agent detects the
   mismatch, reasons about the correction, and records the successful routine.
4. Re-run the same or similar workflow → recall the learned routine → fast
   System-1 handling. Show the **training curve**: time-to-task, intervention
   count, repeat failures, and reasoning calls fall over episodes.

### Phase 4 — Stretch
- **Cross-robot skill transfer:** multiple arms expose standard MCP tools
  (`detect`, `move`, `grip`, `verify`) so a workflow learned on one robot becomes
  a transferable template that can be retested and adapted on another.
- **Synthetic-to-real correction:** compare a simulated plan with real execution,
  then record the physical-world correction as training data.
- Trained **ACT** policy for smooth fast System-1 motion (replaces agent-as-controller
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
