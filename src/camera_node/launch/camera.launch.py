#!/usr/bin/env python3
"""
camera.launch.py - Launch the camera_node with configurable parameters.

Usage:
  # Default (camera 0, 640x480, 15 FPS):
  ros2 launch camera_node camera.launch.py

  # Custom camera index and resolution:
  ros2 launch camera_node camera.launch.py camera_index:=2 width:=1280 height:=720

  # With YAML config file:
  ros2 launch camera_node camera.launch.py camera_config:=/path/to/camera.yaml

Node: camera_node
  Package: camera_node
  Publishes:
    /camera/image_raw   (sensor_msgs/Image)
    /camera/camera_info (sensor_msgs/CameraInfo)
  Parameters:
    camera_index (int)    : USB device index (default: 0)
    width      (int)      : Frame width  (default: 640)
    height     (int)      : Frame height (default: 480)
    fps        (double)   : Target FPS   (default: 15.0)
    frame_id   (string)   : TF frame     (default: 'camera_link')
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_dir = get_package_share_directory('camera_node')
    default_config = os.path.join(pkg_dir, 'config', 'camera.yaml')

    # ---- Launch arguments ----
    camera_config_arg = DeclareLaunchArgument(
        'camera_config',
        default_value=default_config,
        description='Path to camera parameter YAML file'
    )

    camera_index_arg = DeclareLaunchArgument(
        'camera_index',
        default_value='0',
        description='V4L2 camera device index (0 = /dev/video0)'
    )

    width_arg = DeclareLaunchArgument(
        'width',
        default_value='640',
        description='Frame width in pixels'
    )

    height_arg = DeclareLaunchArgument(
        'height',
        default_value='480',
        description='Frame height in pixels'
    )

    fps_arg = DeclareLaunchArgument(
        'fps',
        default_value='15.0',
        description='Target frames per second'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='camera_link',
        description='TF frame ID for image headers'
    )

    # ---- camera_node ----
    camera_node = Node(
        package='camera_node',
        executable='camera_node',
        name='camera_node',
        output='screen',
        parameters=[
            LaunchConfiguration('camera_config'),
            {
                'camera_index': LaunchConfiguration('camera_index'),
                'width': LaunchConfiguration('width'),
                'height': LaunchConfiguration('height'),
                'fps': LaunchConfiguration('fps'),
                'frame_id': LaunchConfiguration('frame_id'),
            },
        ],
    )

    return LaunchDescription([
        camera_config_arg,
        camera_index_arg,
        width_arg,
        height_arg,
        fps_arg,
        frame_id_arg,
        camera_node,
    ])
