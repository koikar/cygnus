# Skill: gripper_open

> Open the gripper to the calibrated open preset.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Measured actual open position around 58-60.

## Procedure (recorded tool calls)

1. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
