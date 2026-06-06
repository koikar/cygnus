# Skill: home_v2

> Go to taught position 'home_v2'.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax → hand-pose → lock).

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=3.1, shoulder_lift=-99.5, elbow_flex=96.7, wrist_flex=16.2, wrist_roll=-96.8, gripper=3.3

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
