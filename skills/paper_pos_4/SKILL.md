# Skill: paper_pos_4

> Go to taught arm position 4 (original calibrated pose).

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Reverted to original taught pose; lateral shifts hurt grabbing. Use adaptive_grab for misplacement.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=-24.3, shoulder_lift=12.2, elbow_flex=27.4, wrist_flex=68.0, wrist_roll=-123.9

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
