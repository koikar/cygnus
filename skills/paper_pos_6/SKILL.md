# Skill: paper_pos_6

> Go to taught arm position 6 (original calibrated pose).

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Reverted to original taught pose; lateral shifts hurt grabbing. Use adaptive_grab for misplacement.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=30.1, shoulder_lift=9.5, elbow_flex=31.2, wrist_flex=67.9, wrist_roll=-70.7

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
