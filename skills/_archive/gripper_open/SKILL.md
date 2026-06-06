# Skill: gripper_open

> Open the gripper to the calibrated open preset.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Measured actual open position around 58-60.

## Procedure (recorded tool calls)

1. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
