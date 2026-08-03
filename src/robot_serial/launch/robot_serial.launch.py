#!/usr/bin/env python3
"""
robot_serial.launch.py - Launch the serial connection node.

Usage:
  ros2 launch robot_serial robot_serial.launch.py

This launch file starts the serial communication node for ESP32 connection.
The node will automatically:
  - Detect available serial ports (/dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyACM0, /dev/ttyACM1)
  - Connect at 115200 baud
  - Read and log incoming data
  - Automatically reconnect if disconnected
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    port_arg = DeclareLaunchArgument(
        'port',
        default_value='auto',
        description='Serial port path (e.g. /dev/ttyUSB0 or auto)'
    )
    baudrate_arg = DeclareLaunchArgument(
        'baudrate',
        default_value='115200',
        description='Serial baudrate'
    )

    serial_node = Node(
        package='robot_serial',
        executable='serial_node',
        name='serial_node',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('port'),
            'baudrate': LaunchConfiguration('baudrate'),
        }]
    )

    return LaunchDescription([
        port_arg,
        baudrate_arg,
        serial_node,
    ])
