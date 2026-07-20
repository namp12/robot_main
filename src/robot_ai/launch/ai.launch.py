#!/usr/bin/env python3
"""
ai.launch.py - Launch the robot_ai vision node.

Usage:
  # Default (detection enabled, 5 FPS):
  ros2 launch robot_ai ai.launch.py

  # With ONNX model:
  ros2 launch robot_ai ai.launch.py model_path:=/path/to/yolo11n.onnx

  # Custom settings:
  ros2 launch robot_ai ai.launch.py confidence_threshold:=0.3 fps_limit:=10.0

Node: robot_ai_node (ai_node)
  Subscribes: /camera/image_raw (sensor_msgs/Image)
  Publishes:
    /robot/ai/detections  (vision_msgs/DetectionArray)
    /robot/ai/status      (vision_msgs/AIStatus)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_dir = get_package_share_directory('robot_ai')
    default_config = os.path.join(pkg_dir, 'config', 'ai.yaml')

    # ---- Launch arguments ----
    ai_config_arg = DeclareLaunchArgument(
        'ai_config',
        default_value=default_config,
        description='Path to AI parameter YAML file'
    )

    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='',
        description='Path to YOLO ONNX model (.onnx or .pt)'
    )

    confidence_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Minimum detection confidence [0.0-1.0]'
    )

    iou_arg = DeclareLaunchArgument(
        'iou_threshold',
        default_value='0.45',
        description='NMS IoU threshold [0.0-1.0]'
    )

    fps_arg = DeclareLaunchArgument(
        'fps_limit',
        default_value='5.0',
        description='Max inference FPS'
    )

    enable_arg = DeclareLaunchArgument(
        'enable_detection',
        default_value='true',
        description='Enable/disable detection'
    )

    gpu_arg = DeclareLaunchArgument(
        'enable_gpu',
        default_value='false',
        description='Enable GPU acceleration (not available on RPi4)'
    )

    # ---- robot_ai_node ----
    ai_node = Node(
        package='robot_ai',
        executable='ai_node',
        name='robot_ai_node',
        output='screen',
        parameters=[
            LaunchConfiguration('ai_config'),
            {
                'model_path': LaunchConfiguration('model_path'),
                'confidence_threshold': LaunchConfiguration('confidence_threshold'),
                'iou_threshold': LaunchConfiguration('iou_threshold'),
                'fps_limit': LaunchConfiguration('fps_limit'),
                'enable_detection': LaunchConfiguration('enable_detection'),
                'enable_gpu': LaunchConfiguration('enable_gpu'),
            },
        ],
    )

    return LaunchDescription([
        ai_config_arg,
        model_path_arg,
        confidence_arg,
        iou_arg,
        fps_arg,
        enable_arg,
        gpu_arg,
        ai_node,
    ])
