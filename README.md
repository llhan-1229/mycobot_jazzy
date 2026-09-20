# myCobot ROS 2 仿真、MoveIt 2 与 MTC 入门

本项目面向 Ubuntu 24.04 和 ROS 2 Jazzy，提供 myCobot 机械臂的 Gazebo
仿真、ROS 2 Control、MoveIt 2 运动规划、RGB-D 感知，以及基于 MoveIt Task
Constructor（MTC）的抓取与放置示例。

本仓库基于
[automaticaddison/mycobot_ros2](https://github.com/automaticaddison/mycobot_ros2)
的 `jazzy` 分支继续开发。

## 本仓库的主要修复和改动

- 移除当前环境中无法加载的 STOMP 规划管线，保留 OMPL 和 Pilz。
- 为 Pilz 增加 `ResolveConstraintFrames`、`ValidateSolution` 和
  `DisplayMotionPath` 适配器，防止规划器把穿过障碍物的轨迹当作成功结果。
- 改进 MTC Fallback 示例：搜索并发布全部完整解，便于在 RViz 中比较
  Cartesian、Pilz 和 OMPL 的回退过程。
- 新增 `mycobot_moveit_studying` 学习包，包含基础 MoveIt 运动和避障示例。
- 扩展感知抓放任务：增加参数校验、服务超时、错误处理、规划统计和
  `execute` 开关。
- 新增一键启动的 `pick_place_system.launch.py`，在启动 MTC 前检查控制器、
  TF、RGB-D 话题、感知服务和执行服务是否就绪。
- 修复多个子 launch 复用 `use_rviz` 等同名参数时的作用域污染问题，使主
  RViz 能稳定加载 Motion Planning Tasks 面板。
- 默认采用“只规划、不执行”模式，避免学习和调试时意外驱动仿真机器人。

## 功能概览

- myCobot 280 的 URDF、SRDF、网格模型和 RViz 配置
- Gazebo Harmonic 仿真和 ROS 2 Control 控制器
- OMPL、Pilz 运动规划与碰撞检测
- MoveIt C++ 接口基础示例
- MoveIt Task Constructor 的 Stage、Container、Fallback 示例
- RGB-D 点云分割、目标识别和 PlanningScene 自动生成
- 从感知、抓取、搬运到放置的完整 MTC 任务

![Gazebo 抓放仿真](https://automaticaddison.com/wp-content/uploads/2024/12/pick-place-gazebo-800-fast.gif)

## 环境要求

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic 与 `ros_gz`
- MoveIt 2
- MoveIt Task Constructor
- PCL 及各 package 在 `package.xml` 中声明的依赖

建议先完成 ROS 2 Jazzy、MoveIt 2 和 Gazebo Harmonic 的安装，并确认以下
命令可用：

```bash
ros2 --help
colcon --help
gz sim --help
```

## 获取和构建

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone -b jazzy https://github.com/llhan-1229/mycobot_ros2.git

cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

每次打开新终端后都要执行：

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

如果修改了源码，请回到工作区根目录重新构建。只构建本仓库的主要包可使用：

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to \
  mycobot_moveit_studying \
  mycobot_mtc_demos \
  mycobot_mtc_pick_place_demo
source install/setup.bash
```

## 推荐上手顺序

### 1. 熟悉机器人描述与坐标系

先阅读以下目录：

- `mycobot_description/urdf`：机器人本体、夹爪和传感器描述
- `mycobot_description/meshes`：机器人和 RealSense D435 模型
- `mycobot_moveit_config/config/mycobot_280`：SRDF、关节限制和运动学配置
- `mycobot_moveit_config/rviz`：MoveIt 的 RViz 配置

查看两个坐标系之间的变换：

```bash
ros2 run tf2_ros tf2_echo base_link gripper_base
```

### 2. 启动 Gazebo 仿真

```bash
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
  load_controllers:=true \
  world_file:=pick_and_place_demo.world \
  use_camera:=true \
  use_rviz:=true \
  use_robot_state_pub:=true \
  use_sim_time:=true
```

如果还要启动 MoveIt，可以在另一个终端运行：

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_moveit_config move_group.launch.py
```

在 RViz 的 MotionPlanning 面板中设置目标姿态并使用 OMPL 规划，可以先建立
对 Planning Group、PlanningScene 和碰撞检测的直观认识。

### 3. 运行基础 MoveIt 示例

```bash
ros2 run mycobot_moveit_studying hi_moveit
ros2 run mycobot_moveit_studying plan_around_objects
```

`hi_moveit` 展示 MoveGroupInterface 的基本规划与执行流程；
`plan_around_objects` 展示如何向 PlanningScene 添加碰撞物体并规划绕障路径。

### 4. 学习 MTC Stage 与 Fallback

仓库提供以下 MTC 示例：

- `alternative_path_costs`
- `cartesian`
- `fallbacks_move_to`
- `ik_clearance_cost`
- `modular`

使用启动脚本运行其中一个示例：

```bash
cd ~/ros2_ws/src/mycobot_ros2
bash mycobot_bringup/scripts/mycobot_280_mtc_demos.sh fallbacks_move_to
```

在 RViz 中打开 `Panels -> Add New Panel -> Motion Planning Tasks - Slider`。
在 Motion Planning Tasks 面板中选择任务和 Solution，再使用 Slider 面板播放
轨迹。播放已有 Solution 只是可视化，不会重新规划，也不会让 Gazebo 中的机械臂
实际运动。

### 5. 运行完整感知抓放系统

建议首先使用默认的只规划模式：

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  execute:=false \
  perception_debug:=false \
  use_rviz:=true
```

系统会依次启动 Gazebo、MoveIt、感知服务和 RViz，等待必要接口就绪，然后启动
MTC 任务。规划成功后可以在 RViz 中检查完整 Stage 树和轨迹。

确认规划结果和碰撞场景正确后，才启用执行：

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  execute:=true \
  perception_debug:=false \
  use_rviz:=true
```

显示额外的实时点云调试窗口：

```bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_system.launch.py \
  execute:=false perception_debug:=true
```

## 完整抓放任务结构

```text
Task
├── current state
├── open gripper
├── move to pick                         [Connect]
├── pick object                          [SerialContainer]
│   ├── approach object                  [MoveRelative]
│   ├── grasp pose IK                    [ComputeIK]
│   │   └── generate grasp pose          [GenerateGraspPose]
│   ├── allow collision
│   ├── close gripper
│   ├── attach object
│   └── lift object
├── move to place                        [Connect]
├── place object                         [SerialContainer]
│   ├── lower object
│   ├── place pose IK                    [ComputeIK]
│   ├── open gripper
│   ├── detach object
│   └── retreat after place
└── move home
```

理解这套任务时，需要区分三类关系：容器的父子层级、Stage 之间的接口状态流，
以及 PropertyMap 的属性继承。它们彼此相关，但不是同一概念。

## 重要配置

- `mycobot_moveit_config/config`：MoveIt、OMPL、Pilz、关节和运动学配置
- `mycobot_mtc_pick_place_demo/config/mtc_node_params.yaml`：抓放目标、距离、
  超时和解数量
- `mycobot_mtc_pick_place_demo/config/get_planning_scene_server.yaml`：点云裁剪、
  聚类和物体识别参数
- `mycobot_mtc_pick_place_demo/launch/pick_place_system.launch.py`：完整系统编排

常用参数：

- `execute`：`false` 只规划和发布轨迹，`true` 执行最佳解
- `max_solutions`：最多生成的完整 MTC 解数量
- `perception_service_timeout`：等待感知服务及响应的超时时间
- `object_dimensions`：目标圆柱体的 `[高度, 半径]`
- `place_pose`：相对 `base_link` 的放置目标
- `approach_object_*`、`lift_object_*`、`retreat_*`：接近、抬升和撤离距离

## 常见问题

### RViz 没有出现或看不到 MTC 面板

确认启动日志中存在 `rviz2` 进程，并检查：

- `use_rviz:=true`
- RViz 已加载 `mtc_demos.rviz`
- Displays 中存在 Motion Planning Tasks
- Panels 中已添加 Motion Planning Tasks - Slider

### `Frame [base_link] does not exist`

检查 `robot_state_publisher`、`/joint_states` 和 TF：

```bash
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo base_link camera_head_link
```

### MoveIt 或控制器没有就绪

```bash
ros2 control list_controllers
ros2 action list
ros2 service list | grep planning_scene
```

`arm_controller`、`gripper_action_controller` 和
`joint_state_broadcaster` 应处于活动状态。

### 感知服务返回失败

确认以下话题有数据：

```bash
ros2 topic hz /camera_head/depth/color/points
ros2 topic hz /camera_head/color/image_raw
```

感知过程会在 `/tmp` 写入若干调试点云。可以这样查看：

```bash
ros2 launch mycobot_mtc_pick_place_demo point_cloud_viewer.launch.py \
  file_name:=/tmp/5_objects_cloud_debug_cloud.pcd
```

### 规划器生成的路径穿过障碍物

不要只看规划器是否返回 `SUCCESS`。还要确认规划管线启用了
`ValidateSolution`，并结合终端碰撞信息、失败 Stage 和 RViz 轨迹共同判断。
本仓库已经为 Pilz 配置完整轨迹验证；当前一个 Fallback 规划器返回无效轨迹时，
后续 OMPL 才会继续尝试绕障。

## 各功能包

| 包 | 用途 |
|---|---|
| `mycobot_description` | URDF、网格模型、传感器和 RViz 描述 |
| `mycobot_gazebo` | Gazebo 世界、模型、相机和仿真启动文件 |
| `mycobot_moveit_config` | MoveIt、SRDF、规划器和控制器配置 |
| `mycobot_moveit_demos` | 基础 MoveIt C++ 示例 |
| `mycobot_moveit_studying` | 本仓库新增的学习和避障示例 |
| `mycobot_mtc_demos` | MTC Stage、代价、Fallback 和模块化示例 |
| `mycobot_mtc_pick_place_demo` | RGB-D 感知与完整抓放任务 |
| `mycobot_interfaces` | 自定义 PlanningScene 服务接口 |
| `mycobot_bringup` | 常用组合启动脚本 |
| `mycobot_system_tests` | 系统级控制测试 |

## 安全提示

- 默认保持 `execute:=false`，先在 RViz 中检查完整轨迹。
- `execute:=true` 会把轨迹发送给控制器；连接真实机器人前必须重新校验关节限制、
  控制器名称、碰撞模型和工作空间。
- RViz 中播放轨迹仅用于可视化，不能等同于控制器执行结果。
