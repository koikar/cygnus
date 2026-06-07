# Skill: paper_pos_1

> Go to taught arm position 1 (original calibrated pose).

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Reverted to original taught pose; lateral shifts hurt grabbing. Use adaptive_grab for misplacement.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=16.8, shoulder_lift=41.6, elbow_flex=-21.8, wrist_flex=81.0, wrist_roll=-80.4

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
