#!/usr/bin/env python3
"""Text-mode teleop for Robot_Tu_Hanh firmware."""

import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

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
    '1': 'mode_manual',
    '2': 'mode_auto',
    't': 't on',
    'g': 'mpu',
    'r': 'reset_goc',
    'h': 'help',
}


class TeleopNode(Node):
    def __init__(self):
        super().__init__('teleop_text')
        self.pub = self.create_publisher(String, '/esp32/serial_tx', 10)
        self.get_logger().info('Teleop ready. Keys: w/a/s/d/q/e/z/c/x, 1/2, t, g, r, h')

    def send(self, text: str):
        msg = String()
        msg.data = text
        self.pub.publish(msg)
        self.get_logger().info(f'[TX] {text}')


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        print('Press keys: w=forward, s=backward, a=strafe left, d=strafe right,')
        print('q=rotate left, e=rotate right, z=diag FL, c=diag FR, x=stop')
        print('1=manual, 2=auto, t=toggle telemetry, g=mpu, r=reset yaw, h=help, Ctrl+C=quit')
        while rclpy.ok():
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x03':
                    break
                cmd = CMD_MAP.get(ch.lower())
                if cmd:
                    node.send(cmd)
                else:
                    node.get_logger().info(f'Unknown key: {ch}')
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
