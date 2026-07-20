#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameters(
            namespace='',
            parameters=[
                ('video_device', '/dev/video0'),
                ('image_width', 640),
                ('image_height', 480),
                ('framerate', 30.0),
                ('pixel_format', 'yuyv'),
                ('camera_name', 'ugreen_camera'),
                ('io_method', 'mmap'),
                ('frame_id', 'camera_link'),
            ],
        )

        self._bridge = CvBridge()
        self._cap = None
        self._publisher = self.create_publisher(Image, 'image_raw', 10)
        self._frame_id = self.get_parameter('frame_id').value
        self._ready = False
        self._retry_count = 0
        self._max_retries = 10
        self._retry_period = 2.0

        self._retry_timer = self.create_timer(self._retry_period, self._retry_camera)
        self._retry_camera()

    def _open_camera(self):
        device = self.get_parameter('video_device').value
        self.get_logger().info(f'Attempting to open camera device: {device}')

        try:
            self._cap = cv2.VideoCapture(device)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.get_logger().error(f'Failed to open camera device {device}: {exc}')
            self._cap = None
            return False

        if not self._cap.isOpened():
            self.get_logger().error(f'Camera device {device} could not be opened')
            self._cap.release()
            self._cap = None
            return False

        width = int(self.get_parameter('image_width').value)
        height = int(self.get_parameter('image_height').value)
        fps = float(self.get_parameter('framerate').value)

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, fps)

        self.get_logger().info(
            f'Camera device {device} opened successfully with {width}x{height} @ {fps} fps'
        )
        return True

    def _retry_camera(self):
        if self._ready:
            return

        if self._retry_count >= self._max_retries:
            self.get_logger().error('Camera device could not be opened after several retries; node will keep running')
            return

        self._retry_count += 1
        if self._open_camera():
            self._timer = self.create_timer(
                1.0 / max(float(self.get_parameter('framerate').value), 1.0),
                self._timer_callback,
            )
            self._ready = True
            self._retry_timer.cancel()
            self.get_logger().info('Camera node started successfully')
        else:
            self.get_logger().warning(
                f'Camera retry {self._retry_count}/{self._max_retries} failed; waiting {self._retry_period}s'
            )

    def _timer_callback(self):
        if self._cap is None:
            return

        ret, frame = self._cap.read()
        if not ret or frame is None:
            self.get_logger().warning('Unable to read frame from camera')
            return

        msg = self._bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        self._publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = CameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f'Camera node error: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
