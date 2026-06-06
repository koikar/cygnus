# Skill: release

> Open the claw to release or prepare to grab.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Gripper-only; pair with grab for pick/place workflows.

## Procedure (recorded tool calls)

1. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
