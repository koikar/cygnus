# Skill: drop_at_3

> Carry to position 3 and open to drop.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Place = pos3 -> release(open=60). Assumes claw already holding.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-16.8, shoulder_lift=56.0, elbow_flex=-44.0, wrist_flex=91.3, wrist_roll=-123.7
2. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
