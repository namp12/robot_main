#!/usr/bin/env python3
"""
robot_all.launch.py - Khởi chạy toàn bộ các Node trên Raspberry Pi (Trừ Lidar).

Usage:
  ros2 launch robot_ai robot_all.launch.py

Bao gồm các Node:
1. command_node: Server HTTP lắng nghe cổng 8001 (Điều khiển động cơ & TTS loa Pi)
2. video_stream_server: Stream Video từ Camera Pi lên PC
3. audio_stream_server: Stream Audio từ Micro Pi lên PC (UDP 5000)
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    http_bridge_node = Node(
        package='robot_ai',
        executable='http_bridge_node',
        name='http_bridge_node',
        output='screen'
    )

    command_node = Node(
        package='robot_ai',
        executable='command_node',
        name='command_node',
        output='screen'
    )

    video_stream_server = Node(
        package='robot_ai',
        executable='video_stream_server',
        name='video_stream_server',
        output='screen'
    )

    audio_stream_server = Node(
        package='robot_ai',
        executable='audio_stream_server',
        name='audio_stream_server',
        output='screen'
    )

    serial_node = Node(
        package='robot_serial',
        executable='serial_node',
        name='serial_node',
        output='screen'
    )

    autonomy_node = Node(
        package='robot_ai',
        executable='autonomy_node',
        name='robot_autonomy_node',
        output='screen',
        parameters=[{'simulation': False, 'autonomy_enabled': False}]
    )

    return LaunchDescription([
        http_bridge_node,
        command_node,
        serial_node,
        video_stream_server,
        audio_stream_server,
        autonomy_node,
    ])
