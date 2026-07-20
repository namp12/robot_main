#!/usr/bin/env python3
"""
robot.launch.py - Master launch file for the autonomous robot.

Launches the complete SLAM stack in one command:
  1. robot_state_publisher  (from robot_description) - publishes TF tree + URDF
  2. sllidar_node           (from sllidar_ros2)       - publishes /scan
  3. slam_toolbox           (from slam_toolbox)       - publishes /map, map->odom TF

This runs on the Raspberry Pi 4.
On the laptop, run view_robot.launch.py separately to open RViz2.

Usage:
  ros2 launch robot_bringup robot.launch.py

Optional arguments:
  serial_port:=/dev/ttyUSB0   (RPLidar USB port)
  use_sim_time:=false         (use sim clock)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    bringup_dir = get_package_share_directory('robot_bringup')
    description_dir = get_package_share_directory('robot_description')

    # ---- Common launch arguments ----
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='USB serial port for RPLidar C1'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    use_static_odom_arg = DeclareLaunchArgument(
        'use_static_odom',
        default_value='true',
        description='Use static odom->base_link (false when ESP32 provides odometry)'
    )

    # ---- Include: robot_state_publisher ----
    robot_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(description_dir, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={
            'use_static_odom': LaunchConfiguration('use_static_odom'),
        }.items(),
    )

    # ---- Include: lidar ----
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'lidar.launch.py')
        ),
        launch_arguments={
            'serial_port': LaunchConfiguration('serial_port'),
        }.items(),
    )

    # ---- Include: SLAM Toolbox ----
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'slam.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
    )

    return LaunchDescription([
        serial_port_arg,
        use_sim_time_arg,
        use_static_odom_arg,
        robot_state_publisher_launch,
        lidar_launch,
        slam_launch,
    ])
