#!/usr/bin/env python3
"""
localization.launch.py - Launch Nav2 AMCL localization with a pre-built map.

Use this AFTER you have saved a map (replacing SLAM Toolbox).

Node: map_server
  Package: nav2_map_server
  Publishes: /map (nav_msgs/OccupancyGrid)
  TF: none

Node: amcl
  Package: nav2_amcl
  Subscribes: /scan (sensor_msgs/LaserScan)
  Publishes: /amcl_pose (geometry_msgs/PoseWithCovarianceStamped)
  TF: map -> odom (AMCL computes this from the map + scan matching)

Prerequisites:
  - A saved map (map.yaml + map.pgm) must exist
  - robot_state_publisher must be running (provides odom->base_link, base_link->laser)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    bringup_dir = get_package_share_directory('robot_bringup')

    # Default map path - on SD card at ~/robot_maps/
    # Override with: ros2 launch robot_bringup localization.launch.py map:=/path/to/map.yaml
    default_map = os.path.expanduser('~/robot_maps/my_room/map.yaml')

    # ---- Launch arguments ----
    map_arg = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Full path to map.yaml file'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    # ---- map_server node ----
    # Loads the map from yaml+pgm and publishes it on /map
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }],
    )

    # ---- lifecycle_manager for map_server ----
    # Nav2 nodes use lifecycle; this manager transitions them to Active
    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': True,
            'node_names': ['map_server'],
        }],
    )

    return LaunchDescription([
        map_arg,
        use_sim_time_arg,
        map_server_node,
        lifecycle_manager_node,
    ])
