# Skill: drop_at_2

> Carry to paper_pos_2 (composed ref), open to drop, lift clear.

**Kind:** place · **Type:** recorded tool-call sequence · **Steps:** 4

## When to use

Composed: references paper_pos. Lift-away avoids knocking the cube on return.

## Procedure (recorded tool calls)

1. `skill` → run `paper_pos_2` (composed reference)
2. `set_gripper` → 60
3. `move_relative` → shoulder_lift=-18.0, elbow_flex=+18.0, wrist_flex=-28.0
4. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
