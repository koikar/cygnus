# Skill: free_space_box_1cm

> Small smooth six-step free-space box around the current pose.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 6

## When to use

Useful as a liveliness/navigation check. It is not exactly closed-loop; expect small drift and re-home or reset after.

## Procedure (recorded tool calls)

1. `move_ee_by` → dx=0, dy=0, dz=0.01
2. `move_ee_by` → dx=0, dy=0.01, dz=0
3. `move_ee_by` → dx=0.01, dy=0, dz=0
4. `move_ee_by` → dx=-0.01, dy=0, dz=0
5. `move_ee_by` → dx=0, dy=-0.01, dz=0
6. `move_ee_by` → dx=0, dy=0, dz=-0.01

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
