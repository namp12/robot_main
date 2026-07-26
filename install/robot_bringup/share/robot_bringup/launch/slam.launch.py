#!/usr/bin/env python3
"""Launch the SLAM Toolbox on top of the minimal robot stack."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_pkg = FindPackageShare('robot_bringup')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true',
    )
    enable_slam_arg = DeclareLaunchArgument(
        'enable_slam',
        default_value='true',
        description='Launch the SLAM Toolbox when true',
    )
    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=PathJoinSubstitution([bringup_pkg, 'config', 'slam_toolbox_params.yaml']),
        description='Path to the slam_toolbox params YAML file',
    )

    minimal_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_pkg, 'launch', 'minimal.launch.py'])
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'enable_lidar': 'true',
            'enable_serial': 'true',
        }.items(),
    )

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
        condition=IfCondition(LaunchConfiguration('enable_slam')),
    )

    return LaunchDescription([
        use_sim_time_arg,
        enable_slam_arg,
        params_file_arg,
        minimal_launch,
        slam_toolbox_node,
    ])
