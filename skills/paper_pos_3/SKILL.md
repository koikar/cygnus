# Skill: paper_pos_3

> Go to taught position 'paper_pos_3'.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax → hand-pose → lock).

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-16.8, shoulder_lift=56.0, elbow_flex=-44.0, wrist_flex=91.3, wrist_roll=-123.7, gripper=17.5

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
