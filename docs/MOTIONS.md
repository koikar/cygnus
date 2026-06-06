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
