# Skill: grab_at_6

> Open, go to paper_pos_6 (composed ref), close to grab.

**Kind:** pick · **Type:** recorded tool-call sequence · **Steps:** 3

## When to use

Composed: references paper_pos so re-teaching the position updates this skill. Open-loop grasp; append a verify_grasp step for a confirmed hold.

## Procedure (recorded tool calls)

1. `set_gripper` → 60
2. `skill` → run `paper_pos_6` (composed reference)
3. `set_gripper` → 15

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
