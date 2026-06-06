# Skill: drop_at_6

> Carry to position 6 and open to drop.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Place = pos6 -> release(open=60). Assumes claw already holding.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=30.1, shoulder_lift=9.5, elbow_flex=31.2, wrist_flex=67.9, wrist_roll=-70.7
2. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
