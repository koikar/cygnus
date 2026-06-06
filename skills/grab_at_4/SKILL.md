# Skill: grab_at_4

> Open, move to position 4, close to grab a cube there.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 3

## When to use

Pick = release -> pos4 -> grab(close=15). Tune close for cube+pads.

## Procedure (recorded tool calls)

1. `set_gripper` → 60
2. `move_to` → shoulder_pan=-24.3, shoulder_lift=12.2, elbow_flex=27.4, wrist_flex=68.0, wrist_roll=-123.9
3. `set_gripper` → 15

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
