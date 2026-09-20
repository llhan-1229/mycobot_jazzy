# Simulation Demonstration Record

Date: 2026-09-16

Environment: ROS 2 Jazzy, Gazebo Harmonic, MoveIt 2, and MoveIt Task Constructor.
RViz was disabled for the automated smoke runs.

## Plan-only run

Command:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  use_rviz:=false execute:=false startup_timeout:=90.0
```

Observed result:

- The readiness gate found joint states, RGB-D topics, camera TF, the planning-scene
  service, both controller actions, and the MTC execution action.
- Perception generated seven collision objects and selected `cylinder_1` as the
  target with a similarity score of `1.00`.
- MTC generated and published a complete solution.
- Execution was explicitly skipped and the simulated robot did not move.

## Execution run

Command:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  use_rviz:=false execute:=true startup_timeout:=90.0
```

Observed result:

- The node reported `Execution mode: enabled`.
- Perception again selected `cylinder_1`, and MTC planning succeeded.
- Arm and gripper controller goals were accepted and all trajectory segments
  completed with MoveIt status `SUCCEEDED`.
- MTC reported `Task executed successfully`.
- Gazebo reported the final `red_cylinder` position as
  `[-0.183415, -0.141170, 0.175000]` m. This matches the configured place XY
  `[-0.183, -0.14]`; Z is the expected half-height of the cylinder.

The test harness stopped the launch with a timeout after the result was recorded.
The simultaneous timeout and manual interrupt produced shutdown-only warnings from
Gazebo and `move_group`; no ROS or Gazebo processes remained afterward.

## Remaining acceptance work

This record proves one plan-only run and one complete execution at the default
cylinder position. It does not claim the three-position, three-runs-per-position
reliability target. That nine-run matrix must still be completed and recorded.
