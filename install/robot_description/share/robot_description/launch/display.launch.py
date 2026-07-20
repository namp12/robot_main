#!/usr/bin/env python3
"""
display.launch.py - Display robot model in RViz2.

This launch file starts the complete visualization stack:

  1. robot_state_publisher
     - Parses robot.urdf.xacro into URDF XML
     - Publishes /robot_description (the full URDF)
     - Publishes /tf_static (all fixed joint transforms)
     - Publishes /tf (transforms for movable joints from /joint_states)

  2. joint_state_publisher
     - Provides a GUI slider for each continuous/revolute joint
     - Publishes /joint_states (sensor_msgs/JointState)
     - Used to manually move wheels/camera in RViz for testing

  3. joint_state_publisher_gui
     - GUI window with sliders for all movable joints
     - Lets you visually test wheel rotation, etc.

  4. rviz2
     - Loads pre-configured rviz.rviz
     - Shows RobotModel, TF tree, LaserScan, Map

Nodes and their roles:
  robot_state_publisher:
    Publishes: /robot_description, /tf, /tf_static
    Subscribes: /joint_states

  joint_state_publisher:
    Publishes: /joint_states
    Subscribes: (none)

  joint_state_publisher_gui:
    Publishes: /joint_states
    Subscribes: (none)

  rviz2:
    Subscribes: /robot_description, /tf, /tf_static, /scan, /map

Launch arguments:
  use_static_odom (bool): Static odom->base_footprint (default: true)
  use_gui (bool): Show joint_state_publisher_gui (default: true)
  rviz_config (str): Path to RViz config file
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    pkg_dir = get_package_share_directory('robot_description')
    default_urdf = os.path.join(pkg_dir, 'urdf', 'robot.urdf.xacro')
    default_rviz = os.path.join(pkg_dir, 'rviz', 'rviz.rviz')

    # ---- Launch arguments ----
    use_static_odom_arg = DeclareLaunchArgument(
        'use_static_odom',
        default_value='true',
        description='Use static odom->base_footprint transform'
    )

    use_gui_arg = DeclareLaunchArgument(
        'use_gui',
        default_value='true',
        description='Show joint_state_publisher_gui window'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz,
        description='Path to RViz2 configuration file'
    )

    # ---- Parse Xacro to URDF ----
    robot_description_content = Command([
        'xacro', ' ', default_urdf,
        ' ', 'use_static_odom:=', LaunchConfiguration('use_static_odom'),
        ' ', 'use_gazebo:=false',
    ])

    # ---- robot_state_publisher ----
    # Publishes /robot_description, /tf, /tf_static
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

    # ---- joint_state_publisher ----
    # Publishes /joint_states for movable joints (left_wheel, right_wheel)
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    # ---- joint_state_publisher_gui ----
    # GUI with sliders for manual joint control
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_gui')),
    )

    # ---- RViz2 ----
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        parameters=[{'use_sim_time': False}],
    )

    return LaunchDescription([
        # Arguments
        use_static_odom_arg,
        use_gui_arg,
        rviz_config_arg,
        # Nodes
        robot_state_publisher_node,
        joint_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ])
