#!/usr/bin/env python3
"""Launch file for Multi-Mode Control System V2 Node."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_mode_arg = DeclareLaunchArgument(
        'default_mode',
        default_value='MANUAL',
        description='Default initial operating mode'
    )

    mode_manager_node = Node(
        package='robot_ai',
        executable='mode_manager_node',
        name='robot_mode_manager_node',
        output='screen',
        parameters=[{
            'default_mode': LaunchConfiguration('default_mode')
        }]
    )

    return LaunchDescription([
        default_mode_arg,
        mode_manager_node
    ])
