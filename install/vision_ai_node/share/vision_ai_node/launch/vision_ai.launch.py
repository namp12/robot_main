#!/usr/bin/env python3
"""
vision_ai.launch.py - Launch the vision_ai_node with configurable parameters.

Usage:
  # Default (detection disabled):
  ros2 launch vision_ai_node vision_ai.launch.py

  # Enable detection with model:
  ros2 launch vision_ai_node vision_ai.launch.py enable_detection:=true model_path:=/path/to/yolov8n.pt

  # Custom confidence and FPS:
  ros2 launch vision_ai_node vision_ai.launch.py enable_detection:=true confidence_threshold:=0.3 max_fps:=3.0

Node: vision_ai_node
  Subscribes: /camera/image_raw (sensor_msgs/Image)
  Publishes:
    /vision/detections      (vision_msgs/DetectionArray)
    /vision/annotated_image  (sensor_msgs/Image)
    /vision/status           (std_msgs/String)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_dir = get_package_share_directory('vision_ai_node')
    default_config = os.path.join(pkg_dir, 'config', 'vision.yaml')

    # ---- Launch arguments ----
    vision_config_arg = DeclareLaunchArgument(
        'vision_config',
        default_value=default_config,
        description='Path to vision parameter YAML file'
    )

    enable_detection_arg = DeclareLaunchArgument(
        'enable_detection',
        default_value='false',
        description='Enable YOLO object detection (true/false)'
    )

    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Minimum confidence for detections [0.0-1.0]'
    )

    max_fps_arg = DeclareLaunchArgument(
        'max_fps',
        default_value='5.0',
        description='Maximum AI processing rate (frames/sec)'
    )

    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='',
        description='Path to YOLO .pt model file'
    )

    publish_image_arg = DeclareLaunchArgument(
        'publish_image',
        default_value='true',
        description='Publish annotated images with bounding boxes'
    )

    # ---- vision_ai_node ----
    vision_ai_node = Node(
        package='vision_ai_node',
        executable='vision_ai_node',
        name='vision_ai_node',
        output='screen',
        parameters=[
            LaunchConfiguration('vision_config'),
            {
                'enable_detection': LaunchConfiguration('enable_detection'),
                'confidence_threshold': LaunchConfiguration('confidence_threshold'),
                'max_fps': LaunchConfiguration('max_fps'),
                'model_path': LaunchConfiguration('model_path'),
                'publish_image': LaunchConfiguration('publish_image'),
            },
        ],
    )

    return LaunchDescription([
        vision_config_arg,
        enable_detection_arg,
        confidence_threshold_arg,
        max_fps_arg,
        model_path_arg,
        publish_image_arg,
        vision_ai_node,
    ])
