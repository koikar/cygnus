# Skill: paper_pos_6

> Go to taught position 'paper_pos_6'.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax → hand-pose → lock).

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=30.1, shoulder_lift=9.5, elbow_flex=31.2, wrist_flex=67.9, wrist_roll=-70.7, gripper=17.5

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
