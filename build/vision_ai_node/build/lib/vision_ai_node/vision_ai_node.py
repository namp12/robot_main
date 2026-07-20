#!/usr/bin/env python3
"""
vision_ai_node.py - AI Vision processing node for ROS2 Humble.

This node subscribes to camera images and runs YOLO object detection.
It does NOT open a webcam directly - it receives images via ROS2 topics
from camera_node.

Subscribed Topics:
  /camera/image_raw (sensor_msgs/Image) - Raw camera frames from camera_node

Published Topics:
  /vision/detections     (vision_msgs/DetectionArray) - Detected objects
  /vision/annotated_image (sensor_msgs/Image)          - Frames with bounding boxes
  /vision/status         (std_msgs/String)              - Node status

Parameters:
  enable_detection   (bool)   : Enable/disable YOLO inference (default: False)
  confidence_threshold (float): Minimum confidence to keep (default: 0.5)
  max_fps            (float)  : Max AI processing rate (default: 5.0)
  model_path         (string) : Path to YOLO .pt model file
  publish_image      (bool)   : Publish annotated images (default: True)

Design:
  - Subscribes to camera, does NOT open webcam
  - FPS throttling: processes at most max_fps frames/sec
  - Lazy model loading: tries to load on init, retries if failed
  - No subscribers check: skips AI if nobody listens
  - Graceful error handling: never crashes the node
"""

import time
from typing import Optional

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

# Import custom messages
from vision_msgs.msg import Detection, DetectionArray


class VisionAINode(Node):
    """
    AI Vision node that runs YOLO object detection on camera frames.

    Receives images via /camera/image_raw (from camera_node),
    runs inference, and publishes detection results.
    """

    def __init__(self) -> None:
        super().__init__('vision_ai_node')

        # ---- Declare ROS2 parameters ----
        self.declare_parameter('enable_detection', False)
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('max_fps', 5.0)
        self.declare_parameter('model_path', '')
        self.declare_parameter('publish_image', True)

        # ---- Read parameters ----
        self._enable_detection: bool = self.get_parameter('enable_detection').value
        self._confidence_threshold: float = self.get_parameter('confidence_threshold').value
        self._max_fps: float = self.get_parameter('max_fps').value
        self._model_path: str = self.get_parameter('model_path').value
        self._publish_image: bool = self.get_parameter('publish_image').value

        # ---- CvBridge for Image <-> OpenCV conversion ----
        self._bridge = CvBridge()

        # ---- YOLO model (lazy loaded) ----
        self._model = None
        self._model_loaded: bool = False
        self._model_load_failed: bool = False

        # ---- FPS throttling ----
        self._min_process_interval: float = 1.0 / max(self._max_fps, 0.1)
        self._last_process_time: float = 0.0

        # ---- Latest frame storage ----
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_stamp = None
        self._latest_frame_id: str = 'camera_link'

        # ---- Publishers ----
        self._det_pub = self.create_publisher(
            DetectionArray, '/vision/detections', 10
        )
        self._img_pub = self.create_publisher(
            Image, '/vision/annotated_image', 5
        )
        self._status_pub = self.create_publisher(
            String, '/vision/status', 10
        )

        # ---- Subscriber ----
        # Subscribe to camera images with QoS profile suitable for real-time
        self._sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self._image_callback,
            10  # QoS depth
        )

        # ---- Processing timer ----
        # Runs at max_fps rate to process the latest frame
        timer_period = self._min_process_interval
        self._process_timer = self.create_timer(timer_period, self._process_timer_callback)

        # ---- Status timer (publish status every 2 seconds) ----
        self._status_timer = self.create_timer(2.0, self._publish_status)

        # ---- Log initialization ----
        self.get_logger().info(
            f'Vision AI node started: enable_detection={self._enable_detection}, '
            f'confidence={self._confidence_threshold}, max_fps={self._max_fps}, '
            f'model_path={self._model_path or "(not set)"}'
        )

        # ---- Attempt to load model ----
        self._load_model()

    def _load_model(self) -> bool:
        """
        Load the YOLO model from the configured path.

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        if not self._model_path:
            self.get_logger().warning(
                'model_path parameter is empty. AI detection disabled. '
                'Set model_path to your YOLO .pt file.'
            )
            self._model_load_failed = True
            return False

        try:
            # Import ultralytics (YOLOv8/YOLO11)
            from ultralytics import YOLO
        except ImportError:
            self.get_logger().error(
                'ultralytics package not installed. '
                'Install with: pip install ultralytics'
            )
            self._model_load_failed = True
            return False

        try:
            self.get_logger().info(f'Loading YOLO model from: {self._model_path}')
            self._model = YOLO(self._model_path)
            self._model_loaded = True
            self._model_load_failed = False

            # Log model info
            model_classes = self._model.names
            self.get_logger().info(
                f'Model loaded successfully: {len(model_classes)} classes. '
                f'First 5: {list(model_classes.values())[:5]}'
            )
            return True

        except Exception as exc:
            self.get_logger().error(
                f'Failed to load YOLO model from {self._model_path}: {exc}'
            )
            self._model = None
            self._model_loaded = False
            self._model_load_failed = True
            return False

    def _image_callback(self, msg: Image) -> None:
        """
        Callback for incoming camera frames.
        Stores the latest frame for the processing timer to use.

        This callback runs at camera FPS (e.g. 15 Hz) but does NOT
        run AI inference - that's done in the processing timer at max_fps.
        """
        try:
            # Convert ROS2 Image to OpenCV BGR
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self._latest_frame = frame
            self._latest_stamp = msg.header.stamp
            self._latest_frame_id = msg.header.frame_id
        except Exception as exc:
            self.get_logger().warning(f'Failed to convert image: {exc}')

    def _process_timer_callback(self) -> None:
        """
        Timer callback: runs at max_fps rate.
        Processes the latest frame with YOLO if enabled.

        Skips processing if:
          - Detection is disabled (enable_detection=false)
          - No frame received yet
          - Model not loaded
          - No subscribers on detection topics
        """
        # ---- Check if detection is enabled ----
        self._enable_detection = self.get_parameter('enable_detection').value
        if not self._enable_detection:
            return

        # ---- Check if model is loaded ----
        if not self._model_loaded or self._model is None:
            # Retry loading if it failed before
            if self._model_load_failed:
                self.get_logger().info('Retrying model load...')
                self._load_model()
            if not self._model_loaded:
                return

        # ---- Check if there are subscribers ----
        # Optimization: don't run AI if nobody is listening
        det_subs = self._det_pub.get_subscription_count()
        img_subs = self._img_pub.get_subscription_count()
        if det_subs == 0 and img_subs == 0:
            return

        # ---- FPS throttle ----
        now = time.time()
        elapsed = now - self._last_process_time
        if elapsed < self._min_process_interval:
            return
        self._last_process_time = now

        # ---- Check if we have a frame ----
        if self._latest_frame is None:
            return

        # ---- Run YOLO inference ----
        self._run_detection(self._latest_frame)

    def _run_detection(self, frame: np.ndarray) -> None:
        """
        Run YOLO detection on a frame and publish results.

        Args:
            frame: OpenCV BGR image from camera.
        """
        try:
            start_time = time.time()

            # Re-read confidence threshold (may have changed dynamically)
            self._confidence_threshold = self.get_parameter('confidence_threshold').value
            self._publish_image = self.get_parameter('publish_image').value

            # Run YOLO inference
            results = self._model(
                frame,
                conf=self._confidence_threshold,
                verbose=False,  # Suppress ultralytics logging
                device='cpu'    # Force CPU (RPi4 has no CUDA)
            )

            inference_time_ms = (time.time() - start_time) * 1000.0

            # ---- Parse detections ----
            det_array = DetectionArray()
            det_array.header.stamp = self._latest_stamp
            det_array.header.frame_id = self._latest_frame_id
            det_array.image_width = frame.shape[1]
            det_array.image_height = frame.shape[0]
            det_array.inference_time_ms = inference_time_ms

            annotated_frame = frame.copy()

            for result in results:
                if result.boxes is None:
                    continue

                boxes = result.boxes
                for i in range(len(boxes)):
                    # Extract bounding box (xyxy format: x_min, y_min, x_max, y_max)
                    box = boxes.xyxy[i].cpu().numpy().astype(int)
                    x_min, y_min, x_max, y_max = box.tolist()

                    # Extract confidence and class
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    cls_name = self._model.names[cls_id]

                    # Create Detection message
                    det = Detection()
                    det.class_name = cls_name
                    det.class_id = cls_id
                    det.confidence = conf
                    det.x_min = x_min
                    det.y_min = y_min
                    det.x_max = x_max
                    det.y_max = y_max
                    det_array.detections.append(det)

                    # Draw bounding box on annotated frame
                    if self._publish_image:
                        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max),
                                      (0, 255, 0), 2)
                        label = f'{cls_name} {conf:.2f}'
                        cv2.putText(annotated_frame, label, (x_min, y_min - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # ---- Publish detections ----
            self._det_pub.publish(det_array)

            # ---- Publish annotated image ----
            if self._publish_image and self._img_pub.get_subscription_count() > 0:
                img_msg = self._bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
                img_msg.header.stamp = self._latest_stamp
                img_msg.header.frame_id = self._latest_frame_id
                self._img_pub.publish(img_msg)

            # ---- Log results ----
            n_det = len(det_array.detections)
            if n_det > 0:
                self.get_logger().debug(
                    f'Detected {n_det} objects in {inference_time_ms:.1f}ms'
                )

        except Exception as exc:
            self.get_logger().error(f'Detection failed: {exc}')
            # Don't crash - will retry on next timer tick

    def _publish_status(self) -> None:
        """
        Publish node status every 2 seconds.
        Status values: "Running", "Idle", "Error"
        """
        status_msg = String()

        if self._model_load_failed:
            status_msg.data = 'Error: model not loaded'
        elif not self._enable_detection:
            status_msg.data = 'Idle: detection disabled'
        elif self._latest_frame is None:
            status_msg.data = 'Idle: no frames received'
        elif self._model_loaded:
            status_msg.data = 'Running'
        else:
            status_msg.data = 'Idle: waiting for model'

        self._status_pub.publish(status_msg)

    def destroy_node(self) -> None:
        """Clean shutdown: cancel timers and release resources."""
        self.get_logger().info('Shutting down vision AI node...')

        if self._process_timer is not None:
            self._process_timer.cancel()
        if self._status_timer is not None:
            self._status_timer.cancel()

        # Release YOLO model
        self._model = None
        self._model_loaded = False

        self.get_logger().info('Vision AI node shut down complete.')
        super().destroy_node()


def main(args: Optional[list] = None) -> None:
    """Entry point: initialize ROS2, create node, spin, cleanup."""
    rclpy.init(args=args)
    node = None

    try:
        node = VisionAINode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        rclpy.logging.get_logger('vision_ai_node').error(f'Fatal error: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
