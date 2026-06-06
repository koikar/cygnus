# Skill: paper_pos_1

> Go to taught position 'paper_pos_1'.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Captured by kinesthetic teaching (relax → hand-pose → lock).

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=16.8, shoulder_lift=41.6, elbow_flex=-21.8, wrist_flex=81.0, wrist_roll=-80.4, gripper=17.4

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
