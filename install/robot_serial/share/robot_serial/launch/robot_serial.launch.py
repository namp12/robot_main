#!/usr/bin/env python3
"""
robot_serial.launch.py - Launch the robot_serial bridge node.

Usage:
  # Default (/dev/ttyACM0, 115200 baud):
  ros2 launch robot_serial robot_serial.launch.py

  # Custom port:
  ros2 launch robot_serial robot_serial.launch.py port:=/dev/ttyUSB0

  # Custom baudrate:
  ros2 launch robot_serial robot_serial.launch.py baudrate:=9600

Node: robot_serial_node
  Package: robot_serial
  Publishes:
    /wheel_encoder    (std_msgs/Int32MultiArray)
    /imu_raw          (sensor_msgs/Imu)
    /battery_voltage  (std_msgs/Float32)
    /wheel_rpm        (std_msgs/Int32MultiArray)
    /robot_status     (std_msgs/String)
  Subscribes:
    /cmd_vel          (geometry_msgs/Twist)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_dir = get_package_share_directory('robot_serial')
    default_config = os.path.join(pkg_dir, 'config', 'serial.yaml')

    # ---- Launch arguments ----
    serial_config_arg = DeclareLaunchArgument(
        'serial_config',
        default_value=default_config,
        description='Path to serial parameter YAML file'
    )

    port_arg = DeclareLaunchArgument(
        'port',
        default_value='/dev/ttyACM0',
        description='Serial port device path'
    )

    baudrate_arg = DeclareLaunchArgument(
        'baudrate',
        default_value='115200',
        description='Serial baud rate'
    )

    timeout_arg = DeclareLaunchArgument(
        'timeout',
        default_value='0.1',
        description='Serial read timeout in seconds'
    )

    reconnect_interval_arg = DeclareLaunchArgument(
        'reconnect_interval',
        default_value='3.0',
        description='Seconds between reconnect attempts'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='base_link',
        description='TF frame ID for IMU messages'
    )

    # ---- robot_serial_node ----
    robot_serial_node = Node(
        package='robot_serial',
        executable='robot_serial_node',
        name='robot_serial_node',
        output='screen',
        parameters=[
            LaunchConfiguration('serial_config'),
            {
                'port': LaunchConfiguration('port'),
                'baudrate': LaunchConfiguration('baudrate'),
                'timeout': LaunchConfiguration('timeout'),
                'reconnect_interval': LaunchConfiguration('reconnect_interval'),
                'frame_id': LaunchConfiguration('frame_id'),
            },
        ],
    )

    return LaunchDescription([
        serial_config_arg,
        port_arg,
        baudrate_arg,
        timeout_arg,
        reconnect_interval_arg,
        frame_id_arg,
        robot_serial_node,
    ])
