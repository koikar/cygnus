# Skill: release

> Open the claw to release or prepare to grab.

**Kind:** primitive · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Gripper-only; pair with grab for pick/place workflows.

## Procedure (recorded tool calls)

1. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
