# ReflexOS Pick-and-Place Benchmark

A resettable, seeded, ground-truth-scored simulation of the reflexos
pick-and-place world — the virtual training field a tedi can be put to the test
in **over MCP**, with no hardware (no arm, no 12V, no tunnel). It is the
simulated counterpart of the physical SO-101: same `reset / observe / act /
score` shape the real arm never had.

## What it models

A cube spawns at one of 6 positions; the arm must pick it and deliver it to a
target bucket (`left` / `right` / `front`). Semantics mirror what we learned on
hardware:

- a grasp succeeds only when the gripper is **aligned with the cube's position**;
- opening over the **target bucket** delivers it (success); opening anywhere
  else drops the cube (a black swan to recover from);
- routing between stops should pass through `home` (a policy-compliance signal);
- `grasp_reliability < 1.0` makes an aligned close occasionally slip, so the task
  requires a **verify-and-retry** loop (the lift-and-verify gate, simulated).

No physics engine, torch, or hardware — pure Python state machine.

## Run it

```bash
# Drive it as an MCP server (a tedi / Claude connects like it did to the arm):
python -m reflexos.benchmark serve                       # stdio
python -m reflexos.benchmark serve --transport http --http-port 8010

# Offline eval (no LLM) — proves the loop + the harness-matters delta:
python -m reflexos.benchmark run --policy skilled --episodes 30
python -m reflexos.benchmark compare --episodes 50 --grasp-reliability 0.7
```

`compare` runs two baseline policies and prints the success delta:

- **blind** — ignores perception, always assumes the cube at one position
  (stand-in for "memory/skills off"); fails when the cube spawned elsewhere.
- **skilled** — reads the observation, grabs at the cube's actual position, and
  verifies the grasp before carrying, retrying on a slip (the full-harness
  behaviour: perceive → act → verify → recover).

Typical result: blind ≈ 1/6 success (only when the cube happens to be at the
assumed spot), skilled ≈ 100% (or ~90% under an unreliable grasp, with more
steps from retries). That gap is the value the learning flywheel is meant to add.

## MCP tool surface

| Tool | Role |
| ---- | ---- |
| `reset_episode(seed?, cube_position?, target_bucket?)` | start a seeded or explicit episode |
| `get_observation()` | perceive ee location, gripper, holding, cube location, target bucket |
| `move_to(target)` | `home` / `pos:1..6` / `bucket:left|right|front` |
| `set_gripper(state)` | `open` / `closed` (grasp at cube, deliver at bucket) |
| `home()` | convenience move to home |
| `score_episode()` | ground-truth verdict: success, delivered, correct_bucket, steps, violations |

## Artifacts

`run` / `compare` write to `outputs/benchmark/`:

- `<policy>_episodes.jsonl` — one **trace bundle per episode** (every tool call +
  observation), the raw-evidence substrate for the harness learning loop;
- `<policy>_scorecard.json` — aggregate success rate, avg steps, violations.

See `tedix/docs/BENCHMARK.md` for how episodes map onto the brain/skills/harness
flywheel (TraceBundle, `memory_feedback`, flywheel snapshots, eval lanes).
