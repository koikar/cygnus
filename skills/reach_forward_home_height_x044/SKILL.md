# Skill: reach_forward_home_height_x044

> Coordinated shoulder/elbow/wrist near-full forward reach to the x≈0.44 m home-height envelope.

**Kind:** primitive · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Validated 2026-06-06: moved FK x from 0.423 m to 0.443 m. Elbow lagged by ~2.8 deg under load; inspect motion.errors and current FK after running.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=0.0, shoulder_lift=30.4, elbow_flex=-43.1, wrist_flex=12.7, wrist_roll=0.0, gripper=60.0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
