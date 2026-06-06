# Skill: grab_at_6

> Open, move to position 6, close to grab.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 3

## When to use

Nominal open-loop grab; adaptive_grab adds vision correction.

## Procedure (recorded tool calls)

1. `set_gripper` → 60
2. `move_to` → shoulder_pan=30.1, shoulder_lift=9.5, elbow_flex=31.2, wrist_flex=67.9, wrist_roll=-70.7
3. `set_gripper` → 15

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
