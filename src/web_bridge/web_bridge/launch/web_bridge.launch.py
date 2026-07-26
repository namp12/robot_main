#!/usr/bin/env python3
"""
web_bridge.launch.py - Launch the ROS2-to-WebSocket bridge node.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    web_bridge_node = Node(
        package='web_bridge',
        executable='web_bridge',
        name='web_bridge_node',
        output='screen',
    )

    return LaunchDescription([
        web_bridge_node,
    ])
