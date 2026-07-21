#!/usr/bin/env python3
"""
Launch file for ESP32 ROS2 Bridge Node.

Usage:
  ros2 launch esp32_ros2_bridge esp32_bridge.launch.py
  
  With custom parameters:
  ros2 launch esp32_ros2_bridge esp32_bridge.launch.py port:=/dev/ttyACM0 baudrate:=115200
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Declare launch arguments
    port_arg = DeclareLaunchArgument(
        'port',
        default_value='/dev/ttyUSB0',
        description='Serial port for ESP32 communication'
    )
    
    baudrate_arg = DeclareLaunchArgument(
        'baudrate',
        default_value='115200',
        description='Serial baudrate'
    )
    
    # ESP32 Bridge Node
    esp32_bridge_node = Node(
        package='esp32_ros2_bridge',
        executable='esp32_bridge_node',
        name='esp32_bridge_node',
        output='screen',
        parameters=[
            {'port': LaunchConfiguration('port')},
            {'baudrate': LaunchConfiguration('baudrate')},
        ],
    )
    
    return LaunchDescription([
        port_arg,
        baudrate_arg,
        esp32_bridge_node,
    ])
