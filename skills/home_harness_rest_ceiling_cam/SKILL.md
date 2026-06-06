# Skill: home_harness_rest_ceiling_cam

> Validated home/rest pose: arm folded backward onto the harness/base area with wrist camera facing upward toward the ceiling.

**Kind:** home · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Validated by scene and wrist snapshots 2026-06-06. This replaces neutral HOME as the physical resting pose. Wrist camera sees ceiling; arm is clear of tabletop and folded back.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=0.0, shoulder_lift=-45.0, elbow_flex=95.0, wrist_flex=-70.0, wrist_roll=0.0, gripper=60.0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
