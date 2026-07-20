"""
camera.py - Camera frame manager for robot_ai.

Subscribes to /camera/image_raw and manages the latest frame.
Runs in a separate thread context (ROS2 callback) to avoid
blocking the inference thread.

Uses a lock-free single-slot buffer pattern:
  - Camera callback writes latest frame (overwrites previous)
  - Inference thread reads latest frame when ready
  - No queuing: we always want the freshest frame

Author: robot
License: Apache-2.0
"""

import threading
import time
from typing import Optional, Tuple

import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CameraManager:
    """
    Manages camera frame subscription and storage.

    Thread-safe: camera callback writes, inference thread reads.
    Uses atomic swap pattern for minimal lock contention.
    """

    def __init__(self, ros_node: Node, image_topic: str) -> None:
        """
        Initialize camera manager.

        Args:
            ros_node: ROS2 node for creating subscription.
            image_topic: Topic name to subscribe (e.g. '/camera/image_raw').
        """
        self._node = ros_node
        self._bridge = CvBridge()

        # ---- Frame storage (single-slot buffer) ----
        self._frame: Optional[np.ndarray] = None
        self._stamp = None
        self._frame_id: str = 'camera_link'
        self._lock = threading.Lock()

        # ---- Statistics ----
        self._frame_count: int = 0
        self._last_fps_time: float = time.time()
        self._camera_fps: float = 0.0

        # ---- Subscribe ----
        self._sub = ros_node.create_subscription(
            Image,
            image_topic,
            self._image_callback,
            10  # QoS depth
        )

        self._node.get_logger().info(f'CameraManager subscribed to: {image_topic}')

    def _image_callback(self, msg: Image) -> None:
        """
        ROS2 callback: convert and store latest frame.

        This runs in the ROS2 executor thread.
        Must be fast - only convert and store.
        """
        try:
            # Convert ROS2 Image -> OpenCV BGR (avoid copy if possible)
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Atomic swap: store frame + metadata under lock
            with self._lock:
                self._frame = frame
                self._stamp = msg.header.stamp
                self._frame_id = msg.header.frame_id

            # Update FPS counter
            self._frame_count += 1
            now = time.time()
            elapsed = now - self._last_fps_time
            if elapsed >= 2.0:
                self._camera_fps = self._frame_count / elapsed
                self._frame_count = 0
                self._last_fps_time = now

        except Exception as exc:
            self._node.get_logger().warning(f'Camera frame conversion failed: {exc}')

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], object, str]:
        """
        Get the latest frame (non-blocking).

        Returns:
            Tuple of (frame, stamp, frame_id).
            frame is None if no frame received yet.
        """
        with self._lock:
            return self._frame, self._stamp, self._frame_id

    def has_frame(self) -> bool:
        """Whether at least one frame has been received."""
        with self._lock:
            return self._frame is not None

    @property
    def camera_fps(self) -> float:
        """Current camera receive rate in FPS."""
        return self._camera_fps

    def destroy(self) -> None:
        """Clean up subscription."""
        if hasattr(self, '_sub') and self._sub is not None:
            self._node.destroy_subscription(self._sub)
            self._sub = None
