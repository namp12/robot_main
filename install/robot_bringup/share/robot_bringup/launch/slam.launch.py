#!/usr/bin/env python3
"""
slam.launch.py - Launch SLAM Toolbox for online async SLAM.

This launch file starts the slam_toolbox node with tuned parameters
for the RPLidar C1 on Raspberry Pi 4.

Node: slam_toolbox
  Package: slam_toolbox
  Subscribes: /scan (sensor_msgs/LaserScan)
  Publishes:  /map (nav_msgs/OccupancyGrid)
  TF:         map -> odom (published by slam_toolbox)

The map->odom transform is computed by SLAM Toolbox based on
scan matching. The odom->base_link transform is currently static
(from robot_state_publisher), and will become dynamic when ESP32
provides real odometry.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    bringup_dir = get_package_share_directory('robot_bringup')

    # ---- Launch arguments ----
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'config', 'slam_toolbox_params.yaml'),
        description='Path to slam_toolbox parameter file'
    )

    # ---- slam_toolbox node ----
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    return LaunchDescription([
        use_sim_time_arg,
        params_file_arg,
        slam_toolbox_node,
    ])
