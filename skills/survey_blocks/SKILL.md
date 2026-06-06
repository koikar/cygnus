# Skill: survey_blocks

> Point the wrist (eye-in-hand) camera down at the block cluster for inspection.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Reliable survey pose: gripper hovers high over the table with the wrist cam framing the blue/cyan/orange blocks. Use as the first step before a pick. Open-loop pose.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=3.0, shoulder_lift=15.0, elbow_flex=6.0, wrist_flex=60.0, wrist_roll=0.0, gripper=50.0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
