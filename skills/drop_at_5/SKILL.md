# Skill: drop_at_5

> Carry to position 5 and open to drop.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Place = pos5 -> release(open=60). Assumes claw already holding.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=1.1, shoulder_lift=-4.2, elbow_flex=47.5, wrist_flex=59.3, wrist_roll=-102.0
2. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
