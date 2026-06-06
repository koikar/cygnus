# Skill: grab_at_1

> Open, move to position 1, close to grab a cube there.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 3

## When to use

Pick = release -> pos1 -> grab(close=15). Tune close for cube+pads.

## Procedure (recorded tool calls)

1. `set_gripper` → 60
2. `move_to` → shoulder_pan=16.8, shoulder_lift=41.6, elbow_flex=-21.8, wrist_flex=81.0, wrist_roll=-80.4
3. `set_gripper` → 15

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
