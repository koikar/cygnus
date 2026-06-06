# Skill: drop_at_1

> Carry to position 1 and open to drop.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Place = pos1 -> release(open=60). Assumes claw already holding.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=16.8, shoulder_lift=41.6, elbow_flex=-21.8, wrist_flex=81.0, wrist_roll=-80.4
2. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
