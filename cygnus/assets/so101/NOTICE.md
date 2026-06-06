SO-101 kinematics URDF
======================

`so101_kinematics.urdf` is a kinematics-only derivative of:

https://github.com/TheRobotStudio/SO-ARM100/blob/main/Simulation/SO101/so101_new_calib.urdf

Changes:

- Removed visual and collision mesh blocks so `placo.RobotWrapper` can load the
  model without STL assets.
- Kept links, joints, transmissions, inertials, joint origins, axes, and limits.

Upstream license: Apache-2.0.
