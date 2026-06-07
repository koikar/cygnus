# Skill: drop_at_bucket

> Carry to the bucket (composed ref), open the claw to release the cube, then lift clear of the rim.

**Kind:** place · **Type:** recorded tool-call sequence · **Steps:** 5

## When to use

Composed: references the `bucket` position so re-teaching it updates this skill. Open releases into the bucket; the shoulder_lift -15 lifts the claw up clear of the rim before any further move.

## Procedure (recorded tool calls)

1. `skill` → run `bucket` (composed reference)
2. `set_gripper` → 60
3. `wait_until_settled`
4. `move_relative` → shoulder_lift=-15.0
5. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the agent-training correction loop that makes the system learning).
