# Skill: clearance_lower_small

> Small downward/forward return from a raised clearance pose.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Only run after clearance_lift_small or from a known raised pose; do not use near the table.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_lift=+8.0, elbow_flex=-8.0, wrist_flex=+10.0
2. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
