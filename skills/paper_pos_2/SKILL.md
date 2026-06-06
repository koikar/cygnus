# Skill: paper_pos_2

> Go to taught arm position 2 (original calibrated pose).

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Reverted to original taught pose; lateral shifts hurt grabbing. Use adaptive_grab for misplacement.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=18.5, shoulder_lift=43.1, elbow_flex=-21.8, wrist_flex=81.4, wrist_roll=-95.5

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
