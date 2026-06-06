# Skill: home_reach_grab_home_demo

> Validated demo route: harness-rest home, stretch forward, move to flex-down tabletop grab pose, close/open gripper, return home.

**Kind:** demo · **Type:** recorded tool-call sequence · **Steps:** 6

## When to use

Run only with the current tabletop layout clear. Home camera points at ceiling; grab uses wrist_flex, not wrist_roll.

## Procedure (recorded tool calls)

1. `move_to` → shoulder_pan=3.1, shoulder_lift=-99.5, elbow_flex=96.7, wrist_flex=16.2, wrist_roll=-96.8
2. `move_to` → shoulder_pan=0.0, shoulder_lift=30.4, elbow_flex=-43.1, wrist_flex=12.7, wrist_roll=0.0, gripper=60.0
3. `move_to` → shoulder_pan=0.0, shoulder_lift=20.0, elbow_flex=-5.0, wrist_flex=35.0, wrist_roll=0.0, gripper=60.0
4. `set_gripper` → 15
5. `set_gripper` → 60
6. `move_to` → shoulder_pan=3.1, shoulder_lift=-99.5, elbow_flex=96.7, wrist_flex=16.2, wrist_roll=-96.8

## Caveats

Open-loop replay: valid only while the target is in the recorded position. If the object has moved, replay will miss the grasp — re-teach the skill (the black-swan → re-learn loop that makes the system antifragile).
