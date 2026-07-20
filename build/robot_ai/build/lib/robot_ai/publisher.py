"""
publisher.py - ROS2 topic publisher for detection results.

Converts detection dictionaries into ROS2 messages and publishes them.
Handles DetectionArray and AIStatus publishing.

Author: robot
License: Apache-2.0
"""

from typing import List, Dict, Any, Optional

from rclpy.node import Node
from vision_msgs.msg import Detection, DetectionArray, AIStatus
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

import numpy as np


class DetectionPublisher:
    """
    Publishes AI detection results to ROS2 topics.

    Topics:
      /robot/ai/detections  - DetectionArray (all detections + metadata)
      /robot/ai/status      - AIStatus (performance metrics)
    """

    def __init__(
        self,
        ros_node: Node,
        detection_topic: str = '/robot/ai/detections',
        status_topic: str = '/robot/ai/status',
    ) -> None:
        """
        Initialize publisher.

        Args:
            ros_node: ROS2 node for creating publishers.
            detection_topic: Topic name for detection results.
            status_topic: Topic name for status updates.
        """
        self._node = ros_node
        self._bridge = CvBridge()

        # ---- Publishers ----
        self._det_pub = ros_node.create_publisher(
            DetectionArray, detection_topic, 10
        )
        self._status_pub = ros_node.create_publisher(
            AIStatus, status_topic, 10
        )

        self._node.get_logger().info(
            f'DetectionPublisher: {detection_topic}, {status_topic}'
        )

    def publish_detections(
        self,
        result: Dict[str, Any],
        stamp,
        frame_id: str,
    ) -> None:
        """
        Publish detection results as DetectionArray message.

        Args:
            result: Detection result dict from Detector.detect()
                Contains 'detections', 'inference_time_ms', etc.
            stamp: ROS2 timestamp from camera frame.
            frame_id: TF frame ID.
        """
        msg = DetectionArray()
        msg.header.stamp = stamp
        msg.header.frame_id = frame_id
        msg.image_width = result.get('image_width', 0)
        msg.image_height = result.get('image_height', 0)
        msg.inference_time_ms = result.get('inference_time_ms', 0.0)

        for det in result.get('detections', []):
            d = Detection()
            d.class_name = det['class_name']
            d.class_id = det['class_id']
            d.confidence = det['confidence']

            bbox = det['bbox']
            d.x_min = int(bbox[0])
            d.y_min = int(bbox[1])
            d.x_max = int(bbox[2])
            d.y_max = int(bbox[3])

            center = det.get('center', [0.0, 0.0])
            d.center_x = float(center[0])
            d.center_y = float(center[1])

            msg.detections.append(d)

        self._det_pub.publish(msg)

    def publish_status(
        self,
        fps: float,
        inference_time_ms: float,
        cpu_usage: float,
        memory_mb: float,
        model_loaded: bool,
        num_detections: int,
        status: str,
    ) -> None:
        """
        Publish AI node status and performance metrics.

        Args:
            fps: Current inference FPS.
            inference_time_ms: Last inference time.
            cpu_usage: CPU usage percentage.
            memory_mb: RAM usage in MB.
            model_loaded: Whether model is ready.
            num_detections: Detection count in last frame.
            status: Status string ("Running", "Idle", "Error").
        """
        msg = AIStatus()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.fps = fps
        msg.inference_time_ms = inference_time_ms
        msg.cpu_usage = cpu_usage
        msg.memory_mb = memory_mb
        msg.model_loaded = model_loaded
        msg.num_detections = num_detections
        msg.status = status

        self._status_pub.publish(msg)

    def has_detection_subscribers(self) -> bool:
        """Check if any node is subscribed to detections."""
        return self._det_pub.get_subscription_count() > 0

    def destroy(self) -> None:
        """Clean up publishers."""
        pass  # ROS2 handles publisher cleanup on node destroy
