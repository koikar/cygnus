# Skill: drop_at_4

> Carry to position 4, open to drop, lift clear.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 4

## When to use

Place + lift-away.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-24.3, shoulder_lift=12.2, elbow_flex=27.4, wrist_flex=68.0, wrist_roll=-123.9
2. `set_gripper` → 60
3. `move_relative` → shoulder_lift=-18.0, elbow_flex=+18.0, wrist_flex=-28.0
4. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
