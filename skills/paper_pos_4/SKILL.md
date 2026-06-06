# Skill: paper_pos_4

> Go to taught position 'paper_pos_4'.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax → hand-pose → lock).

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-24.3, shoulder_lift=12.2, elbow_flex=27.4, wrist_flex=68.0, wrist_roll=-123.9, gripper=17.4

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
