# Skill: paper_pos_2

> Go to taught position 'paper_pos_2'.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax → hand-pose → lock).

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=5.0, shoulder_lift=43.4, elbow_flex=-21.7, wrist_flex=81.6, wrist_roll=-95.8, gripper=17.1

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
