# Skill: home

> Go to the single canonical home: folded back over the harness, wrist camera up, clear of the table.

**Kind:** home · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Arm-only — homing preserves the gripper so a carried object is not dropped. Use set_gripper to open/close explicitly. The home tool targets the same pose.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=3.1, shoulder_lift=-99.5, elbow_flex=96.7, wrist_flex=16.2, wrist_roll=-96.8

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
