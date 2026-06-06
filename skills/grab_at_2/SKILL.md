# Skill: grab_at_2

> Open, move to position 2, close to grab a cube there.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 3

## When to use

Pick = release -> pos2 -> grab(close=15). Tune close for cube+pads.

## Procedure (recorded tool calls)

1. `set_gripper` → 60
2. `move_to` → shoulder_pan=5.0, shoulder_lift=43.4, elbow_flex=-21.7, wrist_flex=81.6, wrist_roll=-95.8
3. `set_gripper` → 15

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
