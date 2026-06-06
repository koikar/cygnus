# Skill: grabbing_motion_practice

> Open-half-close-half-open gripper articulation drill.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 7

## When to use

No object required. Use to test jaw motion and calibration before any grasp attempts.

## Procedure (recorded tool calls)

1. `set_gripper` → 60
2. `set_gripper` → 45
3. `set_gripper` → 30
4. `set_gripper` → 15
5. `set_gripper` → 30
6. `set_gripper` → 45
7. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
