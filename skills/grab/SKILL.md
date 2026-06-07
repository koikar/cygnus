# Skill: grab

> Close the claw to grip an object.

**Kind:** primitive · **Type:** recorded tool-call sequence · **Steps:** 1

## When to use

Gripper-only; independent of arm position. Use after positioning over a target.

## Procedure (recorded tool calls)

1. `set_gripper` → 15

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
