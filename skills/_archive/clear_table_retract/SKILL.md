# Skill: clear_table_retract

> Retract the claw away from the table/cable by folding the arm and reducing nose-down wrist.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

This is the current safe lift-away primitive. Use it when the claw is touching or almost touching the table. It is joint-space by design because Cartesian +Z coupled into sideways/wrist drift near the table.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_lift=-18.0, elbow_flex=+18.0, wrist_flex=-28.0
2. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
