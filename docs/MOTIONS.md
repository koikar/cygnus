# Cygnus motion vocabulary

The SO-101 follower has **6 motors**. Reliable operation comes from layering the
right abstractions on top of them: raw joints → Cartesian end-effector → named
composite skills. The agent should mostly operate at the *highest* layer that
fits, dropping down only when needed.

## The 6 motors (joints)

| Motor (`<joint>.pos`) | Axis | What it does | + direction |
|---|---|---|---|
| `shoulder_pan` | base yaw | swivels the whole arm left/right | (sign TBD by test) |
| `shoulder_lift` | shoulder pitch | raises / lowers the upper arm | + folds arm down/forward |
| `elbow_flex` | elbow pitch | extends / retracts reach | − extends (straightens) |
| `wrist_flex` | wrist pitch | tilts the gripper up / down | + tilts gripper down |
| `wrist_roll` | wrist roll | rotates the jaw orientation | rotates grasp angle |
| `gripper` | jaw | opens / closes the fingers | low = closed, high = open |

> Directions are being mapped empirically and pinned here as confirmed. The wrist
> camera is mounted rotated ~90°, so base-pan appears as *vertical* image motion —
> never reason left/right from the raw wrist frame; use the scene cam or Cartesian.

## Live mapping notes (2026-06-06)

These are empirical notes from the first real SO-101 operation session with the
wrist camera on OpenCV index `0`, scene/laptop camera on index `1`, and the arm
connected at `/dev/tty.usbmodem5A7C1215751`.

| Finding | Operational consequence |
|---|---|
| Positive `shoulder_pan.pos` moved the gripper toward the visible block row in the current scene-camera view. | Use scene camera for lateral alignment; the wrist camera alone is too disorienting. |
| Higher `shoulder_lift.pos` lowered/extended the arm toward the table; lower values lifted/retracted. | Descents must be paired with reach/wrist corrections, not treated as straight-down motion. |
| Lower `elbow_flex.pos` extended reach; higher values bent/retracted. | Avoid max extension near the table unless there is a clear escape path. |
| Higher `wrist_flex.pos` pitched the gripper nose-down. | Useful for approach, but high wrist flex plus full extension can drag into the table/cable. |
| The gripper currently reads about `60` open and `15` closed. | Prefer `set_gripper(position)` while calibrating; `grip(open/close)` is only a preset wrapper. |
| The cable frequently dominates the wrist image. | Do not let vision alignment chase the cable; use the scene camera or segmentation. |

Avoid the stall-prone posture observed during early operation: elbow nearly
straight (`elbow_flex` near `0`), high positive `shoulder_lift` (around `35`),
and high `wrist_flex` (around `90`) near the table/cable. Recover by retracting:
decrease `shoulder_lift`, increase `elbow_flex`, and decrease `wrist_flex`.

## Foundational primitives learned first

Before object work, teach and use these body-only motions:

| Skill | Meaning | Measured note |
|---|---|---|
| `home_harness_rest_ceiling_cam` | `shoulder_lift -45`, `elbow_flex +95`, `wrist_flex -70`, roll neutral, gripper open | The new physical `HOME`: arm folded backward onto the harness/base area, clear of the table, wrist camera looking at the ceiling. |
| `clear_table_retract` | `shoulder_lift -18`, `elbow_flex +18`, `wrist_flex -28`, then settle | Current safe lift-away primitive when the claw is touching or nearly touching the table. |
| `clearance_lift_small` | `shoulder_lift -8`, `elbow_flex +8`, `wrist_flex -10`, then settle | Use only after the claw is already visibly clear; this is a posture/retraction nudge, not a precise Cartesian lift. |
| `clearance_lower_small` | inverse of `clearance_lift_small` | Use only to return from a known raised clearance pose; do not run near the table. |
| `gripper_open` | `set_gripper(60)` | Actual open readings around `58..60`. |
| `gripper_half_close` | `set_gripper(30)` | Actual half-close readings around `28..32`. |
| `gripper_close` | `set_gripper(15)` | Actual closed readings around `16..17`. |
| `grabbing_motion_practice` | open → 45 → 30 → close → 30 → 45 → open | No object required; use to verify jaw articulation before grasp attempts. |

Do **not** treat `move_ee_by(dz=+...)` as the default "lift away from table"
primitive. Near the table, Cartesian `dz` coupled into sideways/wrist movement
and caused contact. Lift away first with `clear_table_retract`; use Cartesian
translation only once the claw is visibly clear, and always run: small nudge →
settle → `get_ee_pose` → decide the next nudge.

## Proprioception: degrees must mean millimeters

The agent must not treat servo degrees as opaque numbers. At any pose, call
`get_joint_effects(step_degrees=1)` before planning joint nudges. It is read-only
FK finite differencing: for each joint it reports how a positive degree changes
the claw in `x/y/z` millimeters and orientation radians. This map is
pose-dependent; recompute it after large moves.

The early "only the claw moves" symptom came from under-commanding the arm:
1 cm Cartesian nudges often solve to only about `2..4` degrees of joint motion,
while the settle tolerance was `3` degrees. The tool could declare success while
the arm barely moved. Use meaningful arm commands and tighter tolerances:

| Situation | Better command style |
|---|---|
| Proving shoulder/base motion | `move_relative({"shoulder_pan.pos": -18}, tolerance=1.0)` then return. |
| Proving elbow/wrist motion | `move_relative({"elbow_flex.pos": -14, "wrist_flex.pos": 14}, tolerance=1.0)` from a clear pose. |
| Small precise correction | Use `get_joint_effects`, choose a joint delta large enough to exceed tolerance, then re-read state. |
| Near table | Run `clear_table_retract` first; do not test tiny Cartesian nudges against the tabletop. |

Live proof from the clear pose: a `shoulder_pan -18` command moved the base about
`17.6°` and returned about `17.3°`; an `elbow_flex -14` / `wrist_flex +14`
command moved about `-11.7°` / `+13.9°` before returning. The arm moves; tiny
commands plus loose tolerances were the no-op pattern.

## Live Jacobian validation

Validation run: `outputs/body_learning/joint_effects_validation_log.json`.
At the clear/retracted pose, we used `get_joint_effects(step_degrees=1)`,
predicted the claw displacement for larger joint commands, executed the commands
with `tolerance=1.0`, then measured the resulting FK pose.

| Command | Predicted claw translation | Measured claw translation | Measured joint motion | Learning |
|---|---:|---:|---:|---|
| `shoulder_lift -10°` | `x +11.6 mm`, `y -19.4 mm`, `z +22.1 mm` | `x +8.9 mm`, `y -14.8 mm`, `z +20.3 mm` | `shoulder_lift -8.9°` | Negative shoulder lift is the cleanest current lift-away lever. |
| `shoulder_pan -12°` | `x +28.3 mm`, `y +16.6 mm`, `z ~0 mm` | `x +24.8 mm`, `y +20.3 mm`, `z -1.2 mm` | `shoulder_pan -11.8°` | Base pan is a real lateral translation control, not a no-op. |
| `wrist_roll +14°` | `x -1.7 mm`, `y -1.0 mm`, `z ~0 mm` | `x -1.8 mm`, `y +0.7 mm`, `z -1.1 mm` | `wrist_roll +13.4°` | Wrist roll mostly spins the jaw; do not use it to move through space. |
| `gripper 60→15→60` | FK translation `0 mm` | close: `~0.03 mm`, open: `0 mm` | `gripper -44.4`, then `+44.2` | Gripper is jaw articulation only; its visibility made it look like the only working motor. |

The finite-difference FK model is not perfect, but it is directionally accurate
enough to plan meaningful moves. It should be treated as proprioception: a live
"what will this servo degree do to the claw right now?" query.

## Home and Grab Validation

Validation run: `outputs/body_learning/home_reach_grab_home_validation_log.json`.
The validated route is:

```text
home_harness_rest_ceiling_cam
→ reach_forward_home_height_x044
→ tabletop_grab_pose_flex_down
→ set_gripper(15)
→ set_gripper(60)
→ home_harness_rest_ceiling_cam
```

Key snapshots:

| Pose | Evidence |
|---|---|
| Home/rest | `outputs/body_learning/images/96_validation_home_return_191619_1_wrist.jpg` shows the wrist camera looking up at the ceiling. |
| Forward stretch | `outputs/body_learning/images/92_validation_reach_forward_191614_2_scene.jpg` shows the arm extended forward from home. |
| Correct grab pose | `outputs/body_learning/images/93_validation_flex_down_grab_pose_191616_2_scene.jpg` shows the claw pitched down using wrist flex. |
| Close/open articulation | `outputs/body_learning/images/94_validation_grab_close_191617_2_scene.jpg` and `95_validation_grab_open_191618_2_scene.jpg` show jaw motion at the corrected pose. |

The corrected tabletop grab posture is:

```json
{
  "shoulder_pan.pos": 0.0,
  "shoulder_lift.pos": 20.0,
  "elbow_flex.pos": -5.0,
  "wrist_flex.pos": 35.0,
  "wrist_roll.pos": 0.0,
  "gripper.pos": 60.0
}
```

Learning: **do not use `wrist_roll` to make the claw "grab downward."** Roll only
twists the jaw. The downward grabbing attitude is `wrist_flex` positive, with
`wrist_roll` kept near neutral. Use `tabletop_grab_pose_flex_down` or
`tabletop_grab_flex_down_close_open`.

## Forward reach validation

Validation run: `outputs/body_learning/validate_forward_reach_chunk_log.json`.
From the high/folded pose
(`shoulder_lift ≈ -71`, `elbow_flex ≈ 97`, `wrist_flex ≈ 7`), the proposed
arm-chain reach command was:

```json
{
  "elbow_flex.pos": -12,
  "shoulder_lift.pos": -4,
  "wrist_flex.pos": -4
}
```

This is **not** a pure forward stretch. It validated as a forward-and-up reach:

| Metric | Result |
|---|---:|
| Predicted translation | `x +29.1 mm`, `y -32.8 mm`, `z +72.5 mm` |
| Measured translation | `x +17.7 mm`, `y -19.4 mm`, `z +62.7 mm` |
| Measured joint motion | `elbow_flex -9.6°`, `shoulder_lift -3.3°`, `wrist_flex -3.3°` |

Learning: at this high pose, reducing `elbow_flex` does extend the arm, but it
also lifts strongly. A true long forward reach should start from a less
high/retracted shoulder pose, then unfold the elbow in larger above-tolerance
chunks while using `shoulder_lift` to hold height and `wrist_flex` to keep claw
attitude useful. Do not include `shoulder_pan` unless changing aim direction.

Follow-up validation run: `outputs/body_learning/home_height_forward_reach_log.json`.
After fixing the FK/IK native dependency pins, the server reported the current
pose as `x=0.423 m`, `z=0.192 m`. Commanding the near-full home-height reach
joint set:

```json
{
  "shoulder_pan.pos": 0.0,
  "shoulder_lift.pos": 30.4,
  "elbow_flex.pos": -43.1,
  "wrist_flex.pos": 12.7,
  "wrist_roll.pos": 0.0,
  "gripper.pos": 60.0
}
```

produced this measured change:

| Metric | Result |
|---|---:|
| FK target for commanded joints | `x=0.440 m`, `z=0.226 m` |
| Actual settled pose | `x=0.443 m`, `z=0.205 m` |
| Measured translation | `x +19.5 mm`, `y -0.1 mm`, `z +12.9 mm` |
| Measured joint motion | `shoulder_lift +13.4°`, `elbow_flex -23.3°`, `wrist_flex +7.6°` |
| Largest residual | `elbow_flex` lagged target by `2.8°` |

This validates Claude's core claim: full forward reach is a **coordinated
shoulder + elbow + wrist** motion, not a single-joint move. It also validates
the torque caveat: near extension, the elbow may settle a few degrees short, so
closed-loop code must inspect `motion.errors` and current FK instead of assuming
the final centimeter is guaranteed.

## Layer 1 — per-joint primitives (fine control)

Relative nudges via `move_relative` (small repeatable deltas, composable):

| Primitive | Joint nudge |
|---|---|
| `pan_left` / `pan_right` | `shoulder_pan` ∓ |
| `shoulder_down` / `shoulder_up` | `shoulder_lift` ± |
| `reach_out` / `reach_in` | `elbow_flex` ∓ |
| `wrist_down` / `wrist_up` | `wrist_flex` ± |
| `roll_cw` / `roll_ccw` | `wrist_roll` ± |
| `open` / `close` | `gripper` |

Pure joint nudges are unreliable for "straight down" (the tip arcs). Use them only
for small corrections; prefer Layer 2 for translations.

## Layer 2 — Cartesian end-effector control (the reliability unlock)

Backed by LeRobot's FK/IK (`RobotKinematics`, placo + the vendored
`cygnus/assets/so101/so101_kinematics.urdf`). This is the layer that makes
operation *reliable* — it removes the hand-eye guessing:

| Tool | Meaning |
|---|---|
| `get_ee_pose()` | end-effector `(x, y, z)` + orientation from FK |
| `move_ee_by(dx, dy, dz)` | translate the gripper in task space (IK → joints) |
| `move_ee_to(x, y, z)` | go to an absolute task-space point |

With these, "move 3 cm toward the cube and 2 cm down" is one call — no joint guessing.
Large Cartesian requests are clipped to a default `0.04 m` step; repeat the same
call for longer moves.

Runtime dependency note: on macOS, `placo>=0.9` currently needs compatible
native `cmeel` packages. Keep `cmeel-urdfdom>=4,<5` and
`cmeel-tinyxml2>=10,<11` in the kinematics extra; newer majors loaded but failed
at runtime because `placo` looked for `liburdfdom_sensor.4.0.dylib` and
`libtinyxml2.10.dylib`.

The server now enforces two guardrails around these tools:

| Guardrail | Meaning |
|---|---|
| Motion lock | Only one actuation command or sequence may run at a time. Concurrent clients fail closed instead of interleaving motor commands. |
| Workspace bounds | `move_ee_to` / `move_ee_by` targets must stay inside the configured base-frame `x/y/z` box, and `max_step_m` is capped by `CYGNUS_MAX_STEP_M`. |

Use `get_capabilities()` or `get_robot_model()` to read the active bounds before
planning. If a Cartesian target comes from vision, project it first and check
`workspace_ok` before moving.

## Layer 2.5 — camera to table calibration

Pixel detections are not robot targets until they are calibrated. The grasping
workflow is:

1. Collect at least four correspondences:

```json
{"pixel": [u, v], "table": [x, y]}
```

2. Save the homography:

```text
fit_table_calibration(correspondences=[...], table_z=<table_z>, camera="scene")
```

3. Convert detections:

```text
detect_colored_blocks(camera="scene")
project_pixel_to_table(u=<center.x>, v=<center.y>, camera="scene")
```

When calibration exists, `detect_colored_blocks` annotates each detection with
`table_target` and `workspace_ok`. That is the grounded path from camera evidence
to a `move_ee_to` target. Without calibration, visual grasping is exploratory and
must not pretend pixel centers are base-frame coordinates.

## Layer 3 — composite workflows (reusable skills / lego pieces)

Built from Layer 2 + gripper. Most are **position-independent** (reusable as-is);
only `align` depends on where the target is.

| Workflow | Composition | Position-independent? |
|---|---|---|
| `home` | go to neutral pose | ✅ |
| `survey` | pose the wrist cam looking down at the workspace | ✅ |
| `align(target)` | center the gripper over a target (vision → `move_ee_by`) | ❌ adaptive |
| `descend_grasp` | `move_ee_by(dz↓)` to contact + `close` | ✅ (flat table) |
| `lift` | `move_ee_by(dz↑)` after grasping | ✅ |
| `place(drop)` | `move_ee_to(drop)` + `open` | ✅ |
| `pick(target)` | `survey → align → descend_grasp → lift` | composes the above |
| `present` | raise the held object toward the scene cam | ✅ |
| `recover` | back off + re-`survey` after a failed grasp (black-swan response) | ✅ |

A pick = `survey → align → descend_grasp → lift → place`. Move the object and only
`align` re-runs; everything else replays as fast one-call skills. When `descend_grasp`
comes up empty (gripper closed, nothing held) that's the **black swan** → `recover`
→ re-`align` → re-learn. That capture/replay/re-learn loop is the antifragility story.
