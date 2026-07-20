#!/usr/bin/env python3
"""
robot_state_publisher.launch.py - Launch only robot_state_publisher.

This is a minimal launch used by robot_bringup/robot.launch.py on the RPi.
It does NOT start RViz or joint_state_publisher_gui.

For full visualization on the laptop, use display.launch.py instead.

Node: robot_state_publisher
  Publishes: /robot_description, /tf, /tf_static
  Subscribes: /joint_states

Launch arguments:
  use_static_odom (bool): Static odom->base_footprint (default: true)
  use_gazebo (bool): Include Gazebo plugins (default: false)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    pkg_dir = get_package_share_directory('robot_description')
    default_urdf = os.path.join(pkg_dir, 'urdf', 'robot.urdf.xacro')

    use_static_odom_arg = DeclareLaunchArgument(
        'use_static_odom',
        default_value='true',
        description='Use static odom->base_footprint transform'
    )

    use_gazebo_arg = DeclareLaunchArgument(
        'use_gazebo',
        default_value='false',
        description='Include Gazebo simulation plugins in URDF'
    )

    robot_description_content = Command([
        'xacro', ' ', default_urdf,
        ' ', 'use_static_odom:=', LaunchConfiguration('use_static_odom'),
        ' ', 'use_gazebo:=', LaunchConfiguration('use_gazebo'),
    ])

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                robot_description_content, value_type=str
            ),
            'use_sim_time': False,
        }],
    )

    return LaunchDescription([
        use_static_odom_arg,
        use_gazebo_arg,
        robot_state_publisher_node,
    ])
