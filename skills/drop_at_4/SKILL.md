# Skill: drop_at_4

> Carry to position 4 and open to drop.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Place = pos4 -> release(open=60). Assumes claw already holding.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-24.3, shoulder_lift=12.2, elbow_flex=27.4, wrist_flex=68.0, wrist_roll=-123.9
2. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
