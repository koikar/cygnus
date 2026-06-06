# Skill: stretch_forward_high_pose

> Stretch the arm forward from the current high/retracted pose using coordinated shoulder, elbow, wrist, and pan.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Measured from high pose: about x +15.6 mm, y +14.9 mm, z -14.1 mm. This is a visible forward reach but not pure +X; call get_joint_effects and adjust for the current pose.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_pan=-6.4, shoulder_lift=+4.5, elbow_flex=+7.3, wrist_flex=-14.0
2. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
