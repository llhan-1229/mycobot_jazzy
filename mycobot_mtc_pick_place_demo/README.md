# myCobot Perception Pick and Place

This package runs the complete simulated pick-and-place pipeline:

1. Gazebo publishes RGB-D data and simulated joint states.
2. The perception service segments the support plane and target cylinder.
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
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py
```

Execute the best solution in Gazebo:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py execute:=true
```

Execute a second, independently perceived and planned task that returns the object
to its initially perceived position:

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  execute:=true repeat_execution:=true
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
- `max_solutions`: maximum number of MTC solutions to generate.
- `perception_service_timeout`: maximum wait for the scene service and response.
- `repeat_execution`: after a successful first execution, re-perceive and return the object.
- `repeat_delay`: wall-clock delay before the second perception request.
- `repeat_perception_retries`, `repeat_perception_retry_delay`: retry policy for transient failures in the return-task perception request.
- `repeat_position_tolerance`: maximum XY error from the first place target before aborting the return task.
- `first_arm_planner_id`, `second_arm_planner_id`: OMPL planners for the two independent tasks.
- `object_dimensions`: expected cylinder `[height, radius]` used for identification.
- `place_pose`: target `[x, y, z, roll, pitch, yaw]` in `base_link`.
- `crop_min_*` and `crop_max_*`: point-cloud region of interest.
- `min_cluster_size`, `cluster_tolerance`: Euclidean clustering controls.
- `circle_radius_tolerance`: cylinder radius matching tolerance.

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
- Perception returns `success=false`: inspect the generated PCD files, then tune
  crop bounds before segmentation and shape tolerances.
- MTC planning fails: inspect failed stages in RViz's Motion Planning Tasks panel.
  Check the grasp transform, approach distances, and place pose before increasing
  timeouts or solution count.

## Acceptance run

For each cylinder position, restart the world, run plan-only once, then run with
`execute:=true` three times. Record perception success, planned stage count,
execution result, and whether the object reached the place pose. The target
acceptance set is three reachable cylinder positions and nine successful executions
without collisions, crashes, or controller aborts.
