# Skill: ee_y_minus_1cm

> Translate the gripper about 1 cm in URDF -Y from the current pose.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Reusable relative free-space nudge; verify with get_ee_pose.

## Procedure (recorded tool calls)

1. `move_ee_by` → dx=0, dy=-0.01, dz=0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay may miss the grasp — use the agent-training loop to correct and save an updated routine.
