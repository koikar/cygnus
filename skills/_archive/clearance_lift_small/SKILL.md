# Skill: clearance_lift_small

> Small upward/retracting clearance nudge from an already safe pose.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Use for smooth navigation only after the claw is already visibly clear. Visually subtle but reduces table-risk posture.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_lift=-8.0, elbow_flex=+8.0, wrist_flex=-10.0
2. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
