#!/usr/bin/env python3
"""Launch file for Autonomous Navigation Stack V3 Engine."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sim_arg = DeclareLaunchArgument(
        'simulation',
        default_value='false',
        description='Set to true for dry-run simulation mode without issuing physical motor commands'
    )

    autonomy_enabled_arg = DeclareLaunchArgument(
        'autonomy_enabled',
        default_value='false',
        description='Enable or disable local autonomy engine'
    )

    autonomy_node = Node(
        package='robot_ai',
        executable='autonomy_node',
        name='robot_autonomy_node',
        output='screen',
        parameters=[{
            'simulation': LaunchConfiguration('simulation'),
            'autonomy_enabled': LaunchConfiguration('autonomy_enabled'),
            'max_linear_speed': 0.35,
            'max_angular_speed': 0.60,
            'inflation_radius': 0.35,
            'sector_count': 36
        }]
    )

    return LaunchDescription([
        sim_arg,
        autonomy_enabled_arg,
        autonomy_node
    ])
