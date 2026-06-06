# Skill: drop_at_1

> Carry to position 1, open to drop, then lift the claw clear of the cube.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 4

## When to use

Place = pos -> release -> lift-away (raise shoulder, retract elbow, wrist up) so the return move doesn't drag the dropped cube.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=16.8, shoulder_lift=41.6, elbow_flex=-21.8, wrist_flex=81.0, wrist_roll=-80.4
2. `set_gripper` → 60
3. `move_relative` → shoulder_lift=-18.0, elbow_flex=+18.0, wrist_flex=-28.0
4. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
