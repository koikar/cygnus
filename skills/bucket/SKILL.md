# Skill: bucket

> Go to the taught bucket drop position (claw positioned over the bucket opening).

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax -> hand-pose -> lock). Arm-only so it preserves the gripper while carrying.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-76.9, shoulder_lift=-22.6, elbow_flex=90.0, wrist_flex=-55.8, wrist_roll=-97.1

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the agent-training correction loop that makes the system learning).
