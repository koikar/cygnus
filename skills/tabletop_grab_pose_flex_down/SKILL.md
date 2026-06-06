# Skill: tabletop_grab_pose_flex_down

> Corrected tabletop pre-grab pose: neutral wrist roll, claw pitched downward using wrist_flex, gripper open.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Validated by snapshot 2026-06-06. Use this before closing; do not use wrist_roll to aim the grab.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=0.0, shoulder_lift=20.0, elbow_flex=-5.0, wrist_flex=35.0, wrist_roll=0.0, gripper=60.0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
