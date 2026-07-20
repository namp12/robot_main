#!/usr/bin/env python3
"""
lidar.launch.py - Launch RPLidar C1 node.

This is the standardized bringup launch for the RPLidar C1M1.
It replaces the original sllidar_ros2 launch with proper parameterization.

Node: sllidar_node
  Package: sllidar_ros2
  Publishes: /scan (sensor_msgs/LaserScan)
  TF: publishes nothing directly; frame_id is set to 'laser'
      (robot_state_publisher handles laser -> base_link transform)

Topics:
  /scan - LaserScan messages with frame_id='laser'
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # ---- Launch arguments ----
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='USB serial port for RPLidar C1'
    )

    serial_baudrate_arg = DeclareLaunchArgument(
        'serial_baudrate',
        default_value='460800',
        description='Serial baudrate (C1 default: 460800)'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='laser',
        description='Frame ID for LaserScan messages (must match URDF laser link name)'
    )

    scan_mode_arg = DeclareLaunchArgument(
        'scan_mode',
        default_value='Standard',
        description='Scan mode: Standard, Express, Boost, Stability'
    )

    # ---- sllidar_node ----
    sllidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[{
            'channel_type': 'serial',
            'serial_port': LaunchConfiguration('serial_port'),
            'serial_baudrate': LaunchConfiguration('serial_baudrate'),
            'frame_id': LaunchConfiguration('frame_id'),
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': LaunchConfiguration('scan_mode'),
        }],
    )

    return LaunchDescription([
        serial_port_arg,
        serial_baudrate_arg,
        frame_id_arg,
        scan_mode_arg,
        sllidar_node,
    ])
