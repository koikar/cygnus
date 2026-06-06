# Skill: forward_up_diagonal_high_pose

> Diagonal forward-and-up reach from the current high pose.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 2

## When to use

Measured from high pose: about x +13.7 mm, y +5.7 mm, z +7.0 mm. Elbow delta was too small to move reliably, so future versions should use larger above-tolerance deltas.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_pan=-4.7, elbow_flex=-1.8, wrist_flex=-4.1
2. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
