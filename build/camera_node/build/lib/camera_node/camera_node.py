#!/usr/bin/env python3
"""
camera_node.py - USB Webcam driver node for ROS2 Humble.

This node is responsible ONLY for capturing images from a USB webcam
(UGREEN UVC) and publishing them as ROS2 Image messages.

It does NOT perform any AI, detection, or processing.
Other nodes subscribe to this node's topics for further processing.

Published Topics:
  /camera/image_raw   (sensor_msgs/Image)       - Raw camera frames
  /camera/camera_info (sensor_msgs/CameraInfo)   - Camera intrinsics metadata

Parameters:
  camera_index (int)    : V4L2 device index (default: 0 -> /dev/video0)
  width      (int)      : Frame width  in pixels (default: 640)
  height     (int)      : Frame height in pixels (default: 480)
  fps        (double)   : Target frames per second  (default: 15.0)
  frame_id   (string)   : TF frame name for headers (default: 'camera_link')

Design:
  - Single class CameraNode(Node) following OOP + SRP
  - Timer-based publishing at configured FPS
  - Auto-reconnect if camera is unplugged
  - Clean shutdown: releases V4L2 device, no Device Busy on restart
  - No threads, no global variables
  - Low CPU/RAM: only reads frames and publishes, no copies
"""

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge


class CameraNode(Node):
    """
    ROS2 node that captures frames from a USB webcam via OpenCV
    and publishes them as sensor_msgs/Image + sensor_msgs/CameraInfo.

    Features:
      - Configurable resolution, FPS, device index via ROS2 parameters
      - Automatic reconnection if the camera is unplugged
      - Graceful shutdown: releases the camera device cleanly
    """

    def __init__(self):
        super().__init__('camera_node')

        # ---- Declare ROS2 parameters ----
        # These can be overridden via launch file or YAML config
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 15.0)
        self.declare_parameter('frame_id', 'camera_link')

        # ---- Read parameter values ----
        self._camera_index = self.get_parameter('camera_index').value
        self._width = self.get_parameter('width').value
        self._height = self.get_parameter('height').value
        self._fps = self.get_parameter('fps').value
        self._frame_id = self.get_parameter('frame_id').value

        # ---- CvBridge: converts OpenCV BGR frames to ROS2 Image messages ----
        self._bridge = CvBridge()

        # ---- Publishers ----
        # Topic: /camera/image_raw - raw image frames
        self._image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        # Topic: /camera/camera_info - camera metadata (resolution, frame_id)
        self._info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        # ---- Camera state ----
        self._cap = None            # cv2.VideoCapture object (None = not opened)
        self._publish_timer = None  # Timer that triggers frame capture + publish
        self._reconnect_timer = None  # Timer for periodic reconnection attempts
        self._consecutive_failures = 0  # Count of failed read() calls in a row
        self._max_failures_before_reconnect = 10  # After this many failures, try reconnect

        # ---- Log startup info ----
        self.get_logger().info(
            f'Camera node initializing: device=/dev/video{self._camera_index}, '
            f'{self._width}x{self._height} @ {self._fps} FPS, frame_id={self._frame_id}'
        )

        # ---- Attempt to open camera ----
        self._open_camera()

        # ---- Start reconnect timer (checks every 3 seconds if camera needs reconnect) ----
        self._reconnect_timer = self.create_timer(3.0, self._check_and_reconnect)

    def _open_camera(self):
        """
        Open the USB webcam using OpenCV VideoCapture.

        Sets resolution and FPS from ROS2 parameters.
        If successful, starts the publish timer.
        If failed, logs error and will retry via reconnect timer.

        Returns:
            bool: True if camera opened successfully, False otherwise.
        """
        device_path = f'/dev/video{self._camera_index}'
        self.get_logger().info(f'Opening camera device: {device_path}')

        try:
            # Use V4L2 backend explicitly for Linux USB cameras
            self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_V4L2)
        except Exception as exc:
            self.get_logger().error(f'Exception while opening {device_path}: {exc}')
            self._cap = None
            return False

        if not self._cap.isOpened():
            self.get_logger().error(
                f'Cannot open camera {device_path}. '
                f'Check: is the camera plugged in? Is another node using it?'
            )
            self._cap.release()
            self._cap = None
            return False

        # ---- Configure camera properties ----
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, self._fps)
        # Use small buffer to avoid stale frames
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # ---- Verify actual settings (some cameras ignore requested values) ----
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)

        self.get_logger().info(
            f'Camera opened successfully: {actual_w}x{actual_h} @ {actual_fps:.1f} FPS '
            f'(requested {self._width}x{self._height} @ {self._fps} FPS)'
        )

        # ---- Reset failure counter ----
        self._consecutive_failures = 0

        # ---- Start publish timer if not already running ----
        if self._publish_timer is None:
            timer_period = 1.0 / max(self._fps, 1.0)
            self._publish_timer = self.create_timer(timer_period, self._timer_callback)
            self.get_logger().info(f'Publish timer started: period={timer_period:.4f}s')

        return True

    def _check_and_reconnect(self):
        """
        Periodic check (every 3 seconds): if camera is disconnected,
        attempt to reopen it. This handles USB unplug events.
        """
        # If camera is already open and working, nothing to do
        if self._cap is not None and self._cap.isOpened():
            return

        self.get_logger().warning(
            'Camera is not open. Attempting to reconnect...'
        )
        # Release any stale capture object
        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._open_camera()

    def _timer_callback(self):
        """
        Timer callback: called at FPS rate.
        Reads one frame from the camera and publishes it.

        If the read fails repeatedly, triggers reconnection.
        """
        # ---- Guard: camera not available ----
        if self._cap is None or not self._cap.isOpened():
            return

        # ---- Read frame from camera ----
        ret, frame = self._cap.read()

        if not ret or frame is None:
            self._consecutive_failures += 1
            if self._consecutive_failures <= 3:
                # Log first few failures as warnings
                self.get_logger().warning(
                    f'Frame read failed ({self._consecutive_failures}/'
                    f'{self._max_failures_before_reconnect})'
                )
            if self._consecutive_failures >= self._max_failures_before_reconnect:
                # Too many failures: camera likely unplugged
                self.get_logger().error(
                    f'Camera read failed {self._consecutive_failures} times. '
                    f'Releasing device for reconnect...'
                )
                self._cap.release()
                self._cap = None
                self._consecutive_failures = 0
            return

        # ---- Reset failure counter on successful read ----
        self._consecutive_failures = 0

        # ---- Convert OpenCV frame (BGR numpy array) to ROS2 Image message ----
        stamp = self.get_clock().now().to_msg()

        image_msg = self._bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        image_msg.header.stamp = stamp
        image_msg.header.frame_id = self._frame_id

        # ---- Build CameraInfo message ----
        info_msg = CameraInfo()
        info_msg.header.stamp = stamp
        info_msg.header.frame_id = self._frame_id
        info_msg.height = frame.shape[0]
        info_msg.width = frame.shape[1]
        info_msg.distortion_model = 'plumb_bob'
        # No calibration data yet - set D, K, R, P to defaults
        info_msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        info_msg.k = [
            float(self._width), 0.0, float(self._width) / 2.0,
            0.0, float(self._height), float(self._height) / 2.0,
            0.0, 0.0, 1.0
        ]
        info_msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info_msg.p = [
            float(self._width), 0.0, float(self._width) / 2.0, 0.0,
            0.0, float(self._height), float(self._height) / 2.0, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]

        # ---- Publish both messages ----
        self._image_pub.publish(image_msg)
        self._info_pub.publish(info_msg)

    def destroy_node(self):
        """
        Clean shutdown: release camera device before destroying the node.
        This prevents "Device Busy" errors when restarting the node.
        """
        self.get_logger().info('Shutting down camera node...')

        # Stop timers
        if self._publish_timer is not None:
            self._publish_timer.cancel()
            self._publish_timer = None

        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()
            self._reconnect_timer = None

        # Release camera device
        if self._cap is not None:
            self.get_logger().info('Releasing camera device...')
            self._cap.release()
            self._cap = None

        self.get_logger().info('Camera node shut down complete.')
        super().destroy_node()


def main(args=None):
    """
    Entry point: initialize ROS2, create node, spin, cleanup.
    """
    rclpy.init(args=args)
    node = None

    try:
        node = CameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        rclpy.logging.get_logger('camera_node').error(f'Fatal error: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
