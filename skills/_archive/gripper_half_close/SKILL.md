# Skill: gripper_half_close

> Move the gripper to a half-closed practice position.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Useful for learning jaw articulation without a full grasp.

## Procedure (recorded tool calls)

1. `set_gripper` → 30

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
