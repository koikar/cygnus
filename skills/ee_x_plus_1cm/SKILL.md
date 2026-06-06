# Skill: ee_x_plus_1cm

> Translate the gripper about 1 cm in URDF +X from the current pose.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 1

## When to use

Reusable relative free-space nudge; verify with get_ee_pose.

## Procedure (recorded tool calls)

1. `move_ee_by` → dx=0.01, dy=0, dz=0

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
