#!/usr/bin/env python3
"""
view_robot.launch.py - Launch RViz2 with pre-configured settings.

Opens RViz2 on the laptop with:
  - Fixed frame: map
  - LaserScan display (topic: /scan, frame: laser)
  - Map display (topic: /map)
  - TF display (shows all TF frames)
  - RobotModel display (shows URDF model)

This launch file runs on the LAPTOP (not on RPi).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    bringup_dir = get_package_share_directory('robot_bringup')
    default_rviz_config = os.path.join(bringup_dir, 'rviz', 'robot_view.rviz')

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config,
        description='Path to RViz2 config file'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        parameters=[{
            'use_sim_time': False,
        }],
    )

    return LaunchDescription([
        rviz_config_arg,
        rviz_node,
    ])
