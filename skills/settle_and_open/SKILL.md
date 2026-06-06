# Skill: settle_and_open

> Wait for the arm to settle, then open the gripper to the calibrated open preset.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Good precondition before free-space navigation or grasp approach.

## Procedure (recorded tool calls)

1. `wait_until_settled`
2. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
