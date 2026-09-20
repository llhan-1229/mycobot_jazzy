#!/usr/bin/env python3
"""Wait until the simulated pick-and-place system is ready for MTC."""

import sys
import time

from control_msgs.action import FollowJointTrajectory, GripperCommand
from moveit_task_constructor_msgs.action import ExecuteTaskSolution
from mycobot_interfaces.srv import GetPlanningScene
import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState, PointCloud2
from tf2_ros import Buffer, TransformListener


class SystemReady(Node):
    """Check ROS interfaces that the perception-driven MTC task requires."""

    def __init__(self):
        super().__init__('mycobot_system_ready')
        self.declare_parameter('timeout', 60.0)
        self.declare_parameter('target_frame', 'base_link')
        self.declare_parameter('camera_frame', 'camera_head_link')

        self.received = {'joint_states': False, 'point_cloud': False, 'rgb_image': False}
        self.create_subscription(
            JointState, '/joint_states',
            lambda _: self._mark_received('joint_states'), 10)
        self.create_subscription(
            PointCloud2, '/camera_head/depth/color/points',
            lambda _: self._mark_received('point_cloud'), 10)
        self.create_subscription(
            Image, '/camera_head/color/image_raw',
            lambda _: self._mark_received('rgb_image'), 10)

        self.scene_client = self.create_client(
            GetPlanningScene, '/get_planning_scene_mycobot')
        self.arm_client = ActionClient(
            self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.gripper_client = ActionClient(
            self, GripperCommand, '/gripper_action_controller/gripper_cmd')
        self.execute_client = ActionClient(
            self, ExecuteTaskSolution, '/execute_task_solution')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def _mark_received(self, name):
        self.received[name] = True

    def missing_interfaces(self):
        missing = [name for name, ready in self.received.items() if not ready]
        if not self.scene_client.service_is_ready():
            missing.append('planning_scene_service')
        if not self.arm_client.server_is_ready():
            missing.append('arm_controller_action')
        if not self.gripper_client.server_is_ready():
            missing.append('gripper_controller_action')
        if not self.execute_client.server_is_ready():
            missing.append('execute_task_solution_action')

        target_frame = self.get_parameter('target_frame').value
        camera_frame = self.get_parameter('camera_frame').value
        if not self.tf_buffer.can_transform(
                target_frame, camera_frame, rclpy.time.Time(), Duration(seconds=0.1)):
            missing.append(f'tf:{camera_frame}->{target_frame}')
        return missing

    def wait(self):
        timeout = self.get_parameter('timeout').value
        deadline = time.monotonic() + timeout
        last_report = 0.0
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            missing = self.missing_interfaces()
            if not missing:
                self.get_logger().info('All pick-and-place interfaces are ready')
                return True
            if time.monotonic() - last_report >= 5.0:
                self.get_logger().info('Waiting for: ' + ', '.join(missing))
                last_report = time.monotonic()

        missing = ', '.join(self.missing_interfaces())
        self.get_logger().error('Startup timed out; missing: ' + missing)
        return False


def main():
    rclpy.init()
    node = SystemReady()
    try:
        success = node.wait()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
