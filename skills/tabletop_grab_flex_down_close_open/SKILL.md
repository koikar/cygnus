# Skill: tabletop_grab_flex_down_close_open

> Correct tabletop grabbing practice: neutral wrist roll, wrist_flex pitches claw downward, close then reopen at table band.

**Type:** robot motion skill (recorded tool-call sequence) · **Steps:** 3

## When to use

Validated by home_reach_grab_home_validation_log.json. This is the corrected replacement for roll/twist based grabbing.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=0.0, shoulder_lift=20.0, elbow_flex=-5.0, wrist_flex=35.0, wrist_roll=0.0, gripper=60.0
2. `set_gripper` → 15
3. `set_gripper` → 60

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
