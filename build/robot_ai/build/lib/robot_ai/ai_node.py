#!/usr/bin/env python3
"""
ai_node.py - Main ROS2 node for AI Vision system.

Orchestrates camera, model, detector, and publisher modules.
Uses a timer-based inference loop that runs at fps_limit rate.

Architecture:
  CameraManager (ROS2 callback thread) -> stores latest frame
  AINode (ROS2 timer thread)           -> reads frame, runs detector, publishes

Threading model:
  - ROS2 executor handles camera callbacks (frame reception)
  - Timer callback runs inference at fps_limit (5-10 FPS)
  - No separate inference thread needed: timer already decouples
    camera rate (15 FPS) from inference rate (5 FPS)

Author: robot
License: Apache-2.0
"""

import os
import time
import threading
from typing import Optional

import rclpy
from rclpy.node import Node

from .config import AIConfig
from .model_loader import ModelLoader
from .detector import Detector
from .camera import CameraManager
from .publisher import DetectionPublisher


class AINode(Node):
    """
    Main AI Vision ROS2 node.

    Subscribes to camera images, runs YOLO detection,
    publishes results and performance status.
    """

    def __init__(self) -> None:
        super().__init__('robot_ai_node')

        # ---- Declare ROS2 parameters ----
        self.declare_parameter('model_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('iou_threshold', 0.45)
        self.declare_parameter('fps_limit', 5.0)
        self.declare_parameter('camera_width', 640)
        self.declare_parameter('camera_height', 480)
        self.declare_parameter('enable_gpu', False)
        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter('enable_detection', True)

        # ---- Load configuration ----
        self._config = AIConfig.from_ros2_params(self)
        try:
            self._config.validate()
        except ValueError as exc:
            self.get_logger().error(f'Invalid config: {exc}')
            raise

        self.get_logger().info(
            f'AI Node config: model={self._config.model_path}, '
            f'conf={self._config.confidence_threshold}, '
            f'fps={self._config.fps_limit}, '
            f'gpu={self._config.enable_gpu}'
        )

        # ---- Initialize modules ----
        # Model loader (loads once, never reloads)
        self._model_loader = ModelLoader(
            model_path=self._config.model_path,
            enable_gpu=self._config.enable_gpu,
            num_threads=1
        )

        # Detector (wraps model with pre/post processing)
        self._detector = Detector(self._model_loader, self._config)

        # Camera manager (subscribes to camera topic)
        self._camera = CameraManager(self, self._config.image_topic)

        # Publisher (publishes results)
        self._publisher = DetectionPublisher(
            self,
            self._config.detection_topic,
            self._config.status_topic,
        )

        # ---- Load model ----
        model_ok = self._model_loader.load()
        if model_ok:
            self._config.class_names = self._model_loader.class_names
            self.get_logger().info(
                f'Model loaded: {self._model_loader.backend}, '
                f'{len(self._config.class_names)} classes'
            )
        else:
            self.get_logger().warning(
                'Model not loaded. Node will run but skip inference. '
                'Set model_path parameter to enable detection.'
            )

        # ---- Performance tracking ----
        self._inference_times = []
        self._last_inference_time = 0.0
        self._fps_actual = 0.0
        self._last_detections_count = 0

        # ---- Inference timer ----
        # Runs at fps_limit rate
        timer_period = 1.0 / max(self._config.fps_limit, 0.1)
        self._inference_timer = self.create_timer(
            timer_period, self._inference_callback
        )

        # ---- Status timer ----
        # Publishes performance metrics every N seconds
        self._status_timer = self.create_timer(
            self._config.status_interval, self._status_callback
        )

        self.get_logger().info(
            f'AI Node ready. Inference timer: {timer_period:.3f}s '
            f'({self._config.fps_limit} FPS target)'
        )

    def _inference_callback(self) -> None:
        """
        Timer callback: runs YOLO inference on latest camera frame.

        Called at fps_limit rate by ROS2 timer.
        Skips if:
          - Detection is disabled
          - Model not loaded
          - No camera frame yet
          - No subscribers on detection topic
        """
        # Check if detection is enabled (can be changed at runtime)
        enable = self.get_parameter('enable_detection').value
        if not enable:
            return

        # Check model
        if not self._model_loader.is_loaded:
            return

        # Skip if no subscribers (save CPU)
        if not self._publisher.has_detection_subscribers():
            return

        # Get latest frame
        frame, stamp, frame_id = self._camera.get_latest_frame()
        if frame is None:
            return

        # Run detection
        try:
            result = self._detector.detect(frame)

            # Update performance stats
            inf_time = result['inference_time_ms']
            self._last_inference_time = inf_time
            self._inference_times.append(inf_time)

            # Keep only last 30 measurements for rolling average
            if len(self._inference_times) > 30:
                self._inference_times.pop(0)

            # Calculate actual FPS
            if len(self._inference_times) >= 2:
                avg_time = sum(self._inference_times) / len(self._inference_times)
                if avg_time > 0:
                    self._fps_actual = 1000.0 / avg_time

            self._last_detections_count = len(result.get('detections', []))

            # Publish results
            self._publisher.publish_detections(result, stamp, frame_id)

            # Debug log
            if self._last_detections_count > 0:
                self.get_logger().debug(
                    f'Detected {self._last_detections_count} objects '
                    f'in {inf_time:.1f}ms'
                )

        except Exception as exc:
            self.get_logger().error(f'Inference failed: {exc}')

    def _status_callback(self) -> None:
        """Timer callback: publish performance status."""
        cpu_usage = self._get_cpu_usage()
        memory_mb = self._get_memory_mb()

        # Determine status string
        enable = self.get_parameter('enable_detection').value
        if not self._model_loader.is_loaded:
            status = 'Error: model not loaded'
        elif not enable:
            status = 'Idle: detection disabled'
        elif not self._camera.has_frame():
            status = 'Idle: no frames'
        else:
            status = 'Running'

        self._publisher.publish_status(
            fps=self._fps_actual,
            inference_time_ms=self._last_inference_time,
            cpu_usage=cpu_usage,
            memory_mb=memory_mb,
            model_loaded=self._model_loader.is_loaded,
            num_detections=self._last_detections_count,
            status=status,
        )

    @staticmethod
    def _get_cpu_usage() -> float:
        """
        Get current process CPU usage percentage.

        Returns:
            CPU usage as percentage [0-100].
        """
        try:
            import resource
            # Use /proc/self/stat for Linux
            with open('/proc/self/stat', 'r') as f:
                parts = f.read().split()
            utime = int(parts[13])
            stime = int(parts[14])
            total_time = utime + stime

            # Get clock ticks per second
            clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

            # Get uptime
            with open('/proc/uptime', 'r') as f:
                uptime = float(f.read().split()[0])

            if uptime > 0:
                cpu_pct = (total_time / clk_tck / uptime) * 100.0
                return min(cpu_pct, 100.0)
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _get_memory_mb() -> float:
        """
        Get current process memory usage in MB.

        Returns:
            Memory usage in megabytes.
        """
        try:
            import resource
            # ru_maxrss is in KB on Linux
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024.0  # KB -> MB
        except Exception:
            pass
        return 0.0

    def destroy_node(self) -> None:
        """Clean shutdown: release all resources."""
        self.get_logger().info('Shutting down AI node...')

        # Cancel timers
        if self._inference_timer is not None:
            self._inference_timer.cancel()
        if self._status_timer is not None:
            self._status_timer.cancel()

        # Clean up modules
        self._camera.destroy()
        self._publisher.destroy()
        self._model_loader.unload()

        self.get_logger().info('AI node shut down complete.')
        super().destroy_node()


def main(args=None) -> None:
    """Entry point."""
    rclpy.init(args=args)
    node = None

    try:
        node = AINode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        rclpy.logging.get_logger('robot_ai').error(f'Fatal error: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
