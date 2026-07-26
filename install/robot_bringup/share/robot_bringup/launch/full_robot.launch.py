#!/usr/bin/env python3
"""Launch the complete robot stack with optional RViz visualization."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_pkg = FindPackageShare('robot_bringup')

    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz2 on the desktop machine when true',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true',
    )
    enable_slam_arg = DeclareLaunchArgument(
        'enable_slam',
        default_value='true',
        description='Launch SLAM Toolbox when true',
    )
    enable_ai_arg = DeclareLaunchArgument(
        'enable_ai',
        default_value='false',
        description='Launch the AI node when true',
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_pkg, 'launch', 'slam.launch.py'])
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'enable_slam': LaunchConfiguration('enable_slam'),
        }.items(),
    )

    ai_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_pkg, 'launch', 'ai.launch.py'])
        ),
        launch_arguments={
            'enable_ai': LaunchConfiguration('enable_ai'),
        }.items(),
    )

    view_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_pkg, 'launch', 'view_robot.launch.py'])
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
    )

    return LaunchDescription([
        use_rviz_arg,
        use_sim_time_arg,
        enable_slam_arg,
        enable_ai_arg,
        slam_launch,
        ai_launch,
        view_launch,
    ])
