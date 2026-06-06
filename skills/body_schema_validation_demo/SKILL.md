# Skill: body_schema_validation_demo

> Demonstrate meaningful shoulder lift and base pan motion using deltas above tolerance.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 8

## When to use

Run only from a clear/retracted pose. This is a validation/demo workflow, not a manipulation primitive. Query get_joint_effects first when planning real moves.

## Procedure (recorded tool calls)

1. `move_relative` → shoulder_lift=-10.0
2. `wait_until_settled`
3. `move_relative` → shoulder_lift=+10.0
4. `wait_until_settled`
5. `move_relative` → shoulder_pan=-12.0
6. `wait_until_settled`
7. `move_relative` → shoulder_pan=+12.0
8. `wait_until_settled`

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
