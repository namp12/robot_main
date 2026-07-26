#!/usr/bin/env python3
"""Launch the AI node as an optional bringup component."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_pkg = FindPackageShare('robot_bringup')
    ai_pkg = FindPackageShare('robot_ai')

    enable_ai_arg = DeclareLaunchArgument(
        'enable_ai',
        default_value='false',
        description='Launch the AI detector when true',
    )
    ai_config_arg = DeclareLaunchArgument(
        'ai_config',
        default_value=PathJoinSubstitution([ai_pkg, 'config', 'ai.yaml']),
        description='Path to the AI parameter YAML file',
    )
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='',
        description='Path to the ONNX or PT model file',
    )

    minimal_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_pkg, 'launch', 'minimal.launch.py'])
        ),
        launch_arguments={
            'enable_lidar': 'false',
            'enable_serial': 'false',
            'publish_robot_description': 'true',
        }.items(),
    )

    ai_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([ai_pkg, 'launch', 'ai.launch.py'])
        ),
        launch_arguments={
            'ai_config': LaunchConfiguration('ai_config'),
            'model_path': LaunchConfiguration('model_path'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('enable_ai')),
    )

    return LaunchDescription([
        enable_ai_arg,
        ai_config_arg,
        model_path_arg,
        minimal_launch,
        ai_launch,
    ])
