#!/usr/bin/env python3
"""Launch the complete Gazebo, MoveIt, perception, and MTC pick-and-place system."""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    execute = LaunchConfiguration('execute')
    repeat_execution = LaunchConfiguration('repeat_execution')
    perception_debug = LaunchConfiguration('perception_debug')
    startup_timeout = LaunchConfiguration('startup_timeout')
    use_rviz = LaunchConfiguration('use_rviz')

    gazebo_share = FindPackageShare('mycobot_gazebo').find('mycobot_gazebo')
    moveit_share = FindPackageShare('mycobot_moveit_config').find('mycobot_moveit_config')
    package_share = FindPackageShare('mycobot_mtc_pick_place_demo').find(
        'mycobot_mtc_pick_place_demo')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            f'{gazebo_share}/launch/mycobot.gazebo.launch.py'),
        launch_arguments={
            'load_controllers': 'true',
            'world_file': 'pick_and_place_demo.world',
            'use_camera': 'true',
            'use_rviz': 'false',
            'use_robot_state_pub': 'true',
            'use_sim_time': 'true',
            'x': '0.0', 'y': '0.0', 'z': '0.0',
            'roll': '0.0', 'pitch': '0.0', 'yaw': '0.0',
        }.items())

    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            f'{moveit_share}/launch/move_group.launch.py'),
        launch_arguments={
            'use_sim_time': 'true',
            'use_rviz': use_rviz,
            'rviz_config_file': 'mtc_demos.rviz',
            'rviz_config_package': 'mycobot_mtc_demos',
        }.items())

    perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            f'{package_share}/launch/get_planning_scene_server.launch.py'),
        launch_arguments={'use_sim_time': 'true'}.items())

    debug_rviz = Node(
        condition=IfCondition(perception_debug),
        package='rviz2',
        executable='rviz2',
        name='perception_debug_rviz',
        arguments=['-d', f'{package_share}/rviz/point_cloud_viewer.rviz'],
        remappings=[('/cloud_pcd', '/camera_head/depth/color/points')],
        parameters=[{'use_sim_time': True}],
        output='screen')

    ready = Node(
        package='mycobot_mtc_pick_place_demo',
        executable='system_ready.py',
        name='mycobot_system_ready',
        parameters=[{'use_sim_time': True, 'timeout': startup_timeout}],
        output='screen')

    def start_task(event, _context):
        if event.returncode != 0:
            return [
                LogInfo(msg='ERROR: System readiness checks failed; MTC will not be started'),
                EmitEvent(event=Shutdown(reason='pick-and-place prerequisites unavailable')),
            ]
        return [
            LogInfo(msg='System ready; starting the perception-driven MTC task'),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    f'{package_share}/launch/pick_place_demo.launch.py'),
                launch_arguments={
                    'use_sim_time': 'true',
                    'execute': execute,
                    'repeat_execution': repeat_execution,
                }.items()),
        ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'execute', default_value='false',
            description='Execute the planned task; false only publishes the solution'),
        DeclareLaunchArgument(
            'repeat_execution', default_value='false',
            description='After a successful execution, re-perceive and return the object'),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Start RViz with the MTC panel'),
        DeclareLaunchArgument(
            'perception_debug', default_value='false',
            description='Start an additional RViz window showing the live RGB-D point cloud'),
        DeclareLaunchArgument(
            'startup_timeout', default_value='90.0',
            description='Seconds to wait for topics, TF, services, and action servers'),
        # Included launch files reuse common argument names such as use_rviz.
        # Scope each include so Gazebo's use_rviz:=false cannot overwrite the
        # top-level value before the MoveIt include evaluates it.
        GroupAction(actions=[gazebo], scoped=True),
        GroupAction(actions=[move_group], scoped=True),
        GroupAction(actions=[perception], scoped=True),
        debug_rviz,
        ready,
        RegisterEventHandler(OnProcessExit(target_action=ready, on_exit=start_task)),
    ])
