#!/usr/bin/env python3
"""Text-mode teleop for Robot_Tu_Hanh firmware and ROS2 /cmd_vel."""

import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

CMD_MAP = {
    'w': 'FORWARD 150',
    's': 'BACKWARD 150',
    'a': 'STRAFE_LEFT 150',
    'd': 'STRAFE_RIGHT 150',
    'q': 'ROTATE_LEFT 150',
    'e': 'ROTATE_RIGHT 150',
    'z': 'DIAGONAL_FRONT_LEFT 150',
    'c': 'DIAGONAL_FRONT_RIGHT 150',
    'x': 'STOP',
    't': 't on',
    'g': 'mpu',
    'r': 'reset_goc',
    'h': 'help',
}

TWIST_MAP = {
    'w': (0.3, 0.0, 0.0),
    's': (-0.3, 0.0, 0.0),
    'a': (0.0, 0.3, 0.0),
    'd': (0.0, -0.3, 0.0),
    'q': (0.0, 0.0, 0.6),
    'e': (0.0, 0.0, -0.6),
    'z': (0.2, 0.2, 0.0),
    'c': (0.2, -0.2, 0.0),
    'x': (0.0, 0.0, 0.0),
}


class TeleopNode(Node):
    def __init__(self):
        super().__init__('teleop_text')
        self.pub = self.create_publisher(String, '/esp32/serial_tx', 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.get_logger().info('Teleop ready. Keys: w/a/s/d/q/e/z/c/x, t, g, r, h')

    def send(self, key: str, text: str):
        # 1. Publish to raw serial_tx
        msg = String()
        msg.data = text
        self.pub.publish(msg)

        # 2. Publish to /cmd_vel
        if key in TWIST_MAP:
            vx, vy, wz = TWIST_MAP[key]
            t = Twist()
            t.linear.x = float(vx)
            t.linear.y = float(vy)
            t.angular.z = float(wz)
            self.cmd_pub.publish(t)

        self.get_logger().info(f'[TX] {text}')


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        print('Press keys: w=forward, s=backward, a=strafe left, d=strafe right,')
        print('q=rotate left, e=rotate right, z=diag FL, c=diag FR, x=stop')
        print('t=toggle telemetry, g=mpu, r=reset yaw, h=help, Ctrl+C=quit')
        while rclpy.ok():
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x03':
                    break
                k = ch.lower()
                cmd = CMD_MAP.get(k)
                if cmd:
                    node.send(k, cmd)
                else:
                    node.get_logger().info(f'Unknown key: {ch}')
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

