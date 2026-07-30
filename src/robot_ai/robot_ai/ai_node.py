#!/usr/bin/env python3
"""
ai_node.py - Simplified AI node (detection removed)

This version removes YOLO/model loading and detection logic per
request. The node remains as a lightweight placeholder in the
`robot_ai` package so other components (e.g. launch files) continue
to work. It logs that detection was removed and exposes a simple
status topic if needed in future.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class AINode(Node):
    def __init__(self) -> None:
        super().__init__('robot_ai_node')
        self.declare_parameter('enable_detection', False)

        # Publisher for a simple status message to indicate node is alive
        self._status_pub = self.create_publisher(String, '/robot/ai/status_simple', 10)

        # Timer to periodically announce status
        self._timer = self.create_timer(5.0, self._timer_callback)
        self.get_logger().info('robot_ai_node started (detection disabled)')

    def _timer_callback(self) -> None:
        msg = String()
        msg.data = 'robot_ai: detection removed — node alive'
        self._status_pub.publish(msg)

    def destroy_node(self) -> None:
        self.get_logger().info('Shutting down simplified AI node')
        if self._timer is not None:
            self._timer.cancel()
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = AINode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
