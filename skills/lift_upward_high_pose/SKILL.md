# Skill: lift_upward_high_pose

> Lift upward from the current high/retracted pose using coupled shoulder, elbow, and wrist.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Measured from high pose: commanded for ~22 mm Z but actual was about z +9.2 mm; elbow lagged under load. Use as a cautious lift/pose change, not a precise vertical move.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_lift=-3.2, elbow_flex=-9.0, wrist_flex=+12.7
2. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
