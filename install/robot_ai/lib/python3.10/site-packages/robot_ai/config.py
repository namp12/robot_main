"""
config.py - Configuration management for robot_ai.

Centralizes all configurable parameters with defaults and validation.
Other modules read config from this class instead of accessing
ROS2 parameters directly.

Author: robot
License: Apache-2.0
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class AIConfig:
    """
    Configuration for the AI Vision system.

    All parameters have sensible defaults for Raspberry Pi 4.
    Can be populated from ROS2 parameters at node startup.
    """

    # ---- Model configuration ----
    # Path to ONNX model file (YOLOv11n exported to ONNX)
    model_path: str = ''

    # Input image size for the model (YOLO expects square)
    model_input_size: int = 640

    # COCO class names (80 classes) - loaded from model metadata
    class_names: list = field(default_factory=list)

    # ---- Detection parameters ----
    # Minimum confidence to keep a detection [0.0 - 1.0]
    confidence_threshold: float = 0.5

    # IoU threshold for Non-Maximum Suppression [0.0 - 1.0]
    iou_threshold: float = 0.45

    # Maximum number of detections per frame
    max_detections: int = 100

    # ---- Performance parameters ----
    # Target FPS for inference (limits CPU usage)
    fps_limit: float = 5.0

    # Camera resolution
    camera_width: int = 640
    camera_height: int = 480

    # Enable GPU acceleration (not available on RPi4, kept for extensibility)
    enable_gpu: bool = False

    # Number of inference threads
    num_threads: int = 1

    # ---- ROS2 configuration ----
    # Topic names
    image_topic: str = '/camera/image_raw'
    detection_topic: str = '/robot/ai/detections'
    status_topic: str = '/robot/ai/status'

    # TF frame ID for detection headers
    frame_id: str = 'camera_link'

    # Status publish rate (seconds)
    status_interval: float = 2.0

    # ---- Feature flags (for future expansion) ----
    # Enable/disable specific features
    enable_tracking: bool = False      # ByteTrack
    enable_ocr: bool = False           # OCR
    enable_face: bool = False          # Face recognition
    enable_qr: bool = False            # QR code detection

    def validate(self) -> bool:
        """
        Validate configuration values.

        Returns:
            bool: True if configuration is valid.

        Raises:
            ValueError: If any parameter is out of range.
        """
        if not 0.0 < self.confidence_threshold <= 1.0:
            raise ValueError(
                f'confidence_threshold must be in (0, 1], got {self.confidence_threshold}'
            )

        if not 0.0 < self.iou_threshold <= 1.0:
            raise ValueError(
                f'iou_threshold must be in (0, 1], got {self.iou_threshold}'
            )

        if self.fps_limit <= 0:
            raise ValueError(f'fps_limit must be positive, got {self.fps_limit}')

        if self.model_input_size <= 0:
            raise ValueError(
                f'model_input_size must be positive, got {self.model_input_size}'
            )

        if self.camera_width <= 0 or self.camera_height <= 0:
            raise ValueError('Camera resolution must be positive')

        return True

    @classmethod
    def from_ros2_params(cls, node) -> 'AIConfig':
        """
        Create AIConfig from ROS2 node parameters.

        Args:
            node: ROS2 Node instance with declared parameters.

        Returns:
            AIConfig populated from ROS2 parameters.
        """
        config = cls()

        config.model_path = node.get_parameter('model_path').value
        config.confidence_threshold = node.get_parameter('confidence_threshold').value
        config.iou_threshold = node.get_parameter('iou_threshold').value
        config.fps_limit = node.get_parameter('fps_limit').value
        config.camera_width = node.get_parameter('camera_width').value
        config.camera_height = node.get_parameter('camera_height').value
        config.enable_gpu = node.get_parameter('enable_gpu').value
        config.frame_id = node.get_parameter('frame_id').value

        return config
