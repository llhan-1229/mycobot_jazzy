# myCobot Perception Pick and Place

This package runs the complete simulated pick-and-place pipeline:

1. Gazebo publishes RGB-D data and simulated joint states.
2. The perception service segments the support plane and red and blue cylinders,
   then identifies the requested color from the aligned RGB-D point cloud.
3. Collision objects are added to the MoveIt planning scene.
4. MoveIt Task Constructor plans the grasp, transfer, place, retreat, and home motions.
5. The plan is visualized in RViz or explicitly executed in Gazebo.

The default mode is plan-only. Execution must be enabled explicitly.

## Prerequisites

- Ubuntu 24.04 with ROS 2 Jazzy
- Gazebo Harmonic and `ros_gz`
- MoveIt 2 and MoveIt Task Constructor
- PCL and the dependencies declared in `package.xml`

Install missing ROS dependencies and build from the workspace root:

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Run

Plan and visualize without moving the simulated robot:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py target_color:=red
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py target_color:=blue
```

`target_color` accepts only `red` or `blue` and defaults to `red`, so the
original launch command continues to select the red cylinder.

Execute the best solution in Gazebo:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  target_color:=blue execute:=true
```

Show a second RViz window with the live camera point cloud:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py perception_debug:=true
```

The launch waits for joint states, RGB image, point cloud, camera TF, perception
service, controller actions, and the MTC execution action. MTC is not started if
any prerequisite remains unavailable at the startup timeout.

## Important parameters

Motion and task parameters are in `config/mtc_node_params.yaml`. Perception
parameters are in `config/get_planning_scene_server.yaml`.

- `execute`: false publishes the solution; true also executes it.
- `target_color`: required cylinder color, `red` or `blue` (default: `red`).
- `non_target_cylinder_padding`: radial safety clearance for unselected cylinders
  (default: `0.006 m`).
- `max_solutions`: maximum number of MTC solutions to generate.
- `perception_service_timeout`: maximum wait for the scene service and response.
- `object_dimensions`: expected cylinder `[height, radius]` used for identification.
- `place_pose`: target `[x, y, z, roll, pitch, yaw]` in `base_link`.
- `crop_min_*` and `crop_max_*`: point-cloud region of interest.
- `min_cluster_size`, `cluster_tolerance`: Euclidean clustering controls.
- `circle_radius_tolerance`: cylinder radius matching tolerance.
- `color_min_saturation`: minimum HSV saturation included in color voting
  (default: `0.4`).
- `color_min_value`: minimum HSV brightness included in color voting
  (default: `0.1`).
- `color_min_confidence`: minimum fraction of eligible points voting for the
  winning supported color (default: `0.6`).

The red cylinder is centered at `(0.22, 0.12, 0.175)` and the blue cylinder at
`(0.12, 0.22, 0.175)` in the Gazebo world. Both are on a horizontal radius of
about `0.2506 m` from `base_link`; their centers are about `0.141 m` apart.
Both colors use the same configured `place_pose`. Every detected object is added
to the MoveIt planning scene, so the cylinder that was not selected remains a
collision obstacle. Non-target cylinders are padded by `0.006 m` because the
RGB-visible radii are slightly smaller than the Gazebo collision geometry.

Color matching is strict. Low-saturation and low-brightness points are ignored;
if the requested color is absent, unknown, or below the confidence threshold,
the perception service returns failure instead of selecting another object by
shape alone. Shape and dimension similarity are evaluated only after color
matching.

## Perception debugging

Each planning-scene request writes intermediate clouds to `/tmp`:

- `/tmp/4_convertToPCL_debug_cloud.pcd`
- `/tmp/5_support_plane_debug_cloud.pcd`
- `/tmp/5_objects_cloud_debug_cloud.pcd`

Open one with:

```bash
ros2 launch mycobot_mtc_pick_place_demo point_cloud_viewer.launch.py \
  file_name:=/tmp/5_objects_cloud_debug_cloud.pcd
```

## Troubleshooting

- `point_cloud` or `rgb_image` missing: confirm `use_camera:=true` and inspect
  `/camera_head/depth/color/points` and `/camera_head/color/image_raw`.
- Camera TF missing: run `ros2 run tf2_ros tf2_echo base_link camera_head_link`.
- Controller action missing: inspect `ros2 control list_controllers`; the arm,
  gripper, and joint state broadcaster must be active.
- Perception returns `success=false`: confirm the requested cylinder is visible
  and inspect the generated PCD files. Tune the HSV confidence thresholds, crop
  bounds, or shape tolerances as indicated by the detection logs.
- MTC planning fails: inspect failed stages in RViz's Motion Planning Tasks panel.
  Check the grasp transform, approach distances, and place pose before increasing
  timeouts or solution count.

## Acceptance run

For each target color, restart the world, run plan-only once, then run once with
`execute:=true`. Confirm the perception log reports the requested color and
target ID, the complete MTC task is planned, the selected cylinder reaches the
configured place pose, and the other cylinder remains at its original position.
Both executions must complete without a collision or controller abort.

The current implementation was verified with the following results:

- Color and target-selection unit tests: 7/7 passed, including pure red/blue,
  dark colors, achromatic noise, low confidence, unsupported colors, missing
  targets, and same-size red/blue selection.
- `target_color:=red` plan-only: selected `cylinder_1`, red confidence `1.000`,
  25 complete MTC solutions.
- `target_color:=blue` plan-only: selected `cylinder_2`, blue confidence `1.000`,
  25 complete MTC solutions.
- Red execution: the red cylinder reached approximately
  `(-0.1832, -0.1435, 0.175)` and the blue cylinder stayed at
  `(0.12, 0.22, 0.175)`.
- Blue execution: the blue cylinder reached approximately
  `(-0.1840, -0.1420, 0.175)` and the red cylinder stayed at
  `(0.22, 0.12, 0.175)`.

The controller reported `SUCCEEDED` for both executions and MTC reported
`Task executed successfully`. On shutdown, this ROS/Gazebo setup may emit a
MoveIt SIGINT cleanup warning after the task has already completed; it does not
indicate a planning or controller failure.

The package's existing aggregate lint baseline still reports flake8, pep257,
and uncrustify failures in legacy files. The feature-specific build, unit
tests, interface tests, launch syntax checks, and `git diff --check` pass.
