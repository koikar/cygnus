# Skill: retract_forward_stage_x042

> Retract from near-full forward reach back toward the x≈0.42 m staged reach posture.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Validated 2026-06-06 after x044 stretch. Shoulder_lift may lag several degrees; use get_ee_pose after running.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=0.0, shoulder_lift=15.8, elbow_flex=-20.9, wrist_flex=5.1, wrist_roll=0.0, gripper=60.0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
