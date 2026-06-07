# Skill: bucket

> Go to the bucket drop position (bucket now IN FRONT of the arm, full forward stretch at bucket height).

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Kinesthetically taught: front full-stretch at bucket-rim height (front-facing like pos 2 but elevated). Arm-only so it preserves the grip while carrying. drop_at_bucket keeps the open->lift-clear movement via composition.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=2.5, shoulder_lift=62.5, elbow_flex=-60.4, wrist_flex=16.1, wrist_roll=-96.8

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the agent-training correction loop that makes the system learning).
