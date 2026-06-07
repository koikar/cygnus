# Skill: bucket

> Go to the bucket drop position (LEFT of home), raised so the cube clears the box rim.

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Left-side reach, raised shoulder_lift to -34. Arm-only.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-76.9, shoulder_lift=-34.0, elbow_flex=90.0, wrist_flex=-55.8, wrist_roll=-97.1

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the agent-training correction loop that makes the system learning).
