# Skill: paper_pos_5

> Go to taught arm position 5 (original calibrated pose).

**Kind:** position · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Reverted to original taught pose; lateral shifts hurt grabbing. Use adaptive_grab for misplacement.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=1.1, shoulder_lift=-4.2, elbow_flex=47.5, wrist_flex=59.3, wrist_roll=-102.0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
