# Skill: drop_at_bucket

> Carry to the bucket (composed ref), open to release, then raise high to clear the rim before any backward motion.

**Kind:** place · **Type:** recorded tool-call sequence · **Steps:** 5

## When to use

Composed: references the `bucket` position. Open releases the cube; shoulder_lift -45 lifts the claw well above the bucket rim (was -15, which dragged the claw through the rim on retract) so the subsequent home fold stays above the bucket.

## Procedure (recorded tool calls)

1. `skill` → run `bucket` (composed reference)
2. `set_gripper` → 60
3. `wait_until_settled`
4. `move_relative` → shoulder_lift=-45.0
5. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the agent-training correction loop that makes the system learning).
