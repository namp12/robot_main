#!/usr/bin/env python3
"""Launch wheel odometry node for /wheel_rpm -> /odom."""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    port_arg = DeclareLaunchArgument(
        'wheel_radius',
        default_value='0.033',
        description='Wheel radius in meters'
    )

    separation_arg = DeclareLaunchArgument(
        'wheel_separation',
        default_value='0.30',
        description='Distance between left and right wheels in meters'
    )

    odom_frame_arg = DeclareLaunchArgument(
        'odom_frame',
        default_value='odom',
        description='Odometry frame ID'
    )

    base_frame_arg = DeclareLaunchArgument(
        'base_frame',
        default_value='base_footprint',
        description='Robot base frame ID'
    )

    publish_rate_arg = DeclareLaunchArgument(
        'publish_rate',
        default_value='20.0',
        description='Odometry publish rate in Hz'
    )

    wheel_odom_node = Node(
        package='robot_serial',
        executable='wheel_odom_node',
        name='wheel_odometry_node',
        output='screen',
        parameters=[
            {'wheel_radius': LaunchConfiguration('wheel_radius')},
            {'wheel_separation': LaunchConfiguration('wheel_separation')},
            {'odom_frame': LaunchConfiguration('odom_frame')},
            {'base_frame': LaunchConfiguration('base_frame')},
            {'publish_rate': LaunchConfiguration('publish_rate')},
        ],
    )

    return LaunchDescription([
        port_arg,
        separation_arg,
        odom_frame_arg,
        base_frame_arg,
        publish_rate_arg,
        wheel_odom_node,
    ])
