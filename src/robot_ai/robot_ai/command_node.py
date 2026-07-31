import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist


class CommandNode(Node):

    def __init__(self):
        super().__init__('robot_command_node')

        self.subscription = self.create_subscription(
            String,
            '/robot/command',
            self.command_callback,
            10
        )

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.last_motion_time = None
        self.last_cmd = Twist()
        self.motion_timeout_sec = 1.0
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_callback)

        self.get_logger().info('Robot command node ONLINE')

    def command_callback(self, msg):
        text = msg.data.strip().lower()
        self.get_logger().info(f'COMMAND RECEIVED: {msg.data}')

        cmd = Twist()

        if text in ['đi thẳng', 'di thang', 'tiến', 'tien', 'forward', 'tiens_len']:
            cmd.linear.x = 0.20

        elif text in ['lùi', 'lui', 'lùi lại', 'lui lai', 'back', 'backward', 'lui_lai']:
            cmd.linear.x = -0.20

        elif text in ['trái', 'trai', 'left', 'quay_trai']:
            cmd.angular.z = 0.50

        elif text in ['phải', 'phai', 'right', 'quay_phai']:
            cmd.angular.z = -0.50

        elif text in ['dừng', 'dung', 'stop', 'giu_nguyen']:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        else:
            self.get_logger().warn(f'UNKNOWN COMMAND: {msg.data}')
            return

        self.cmd_vel_pub.publish(cmd)
        self.last_cmd = cmd
        self.last_motion_time = self.get_clock().now()

        self.get_logger().info(
            f'CMD_VEL: linear.x={cmd.linear.x:.2f}, angular.z={cmd.angular.z:.2f}'
        )

    def watchdog_callback(self):
        if self.last_motion_time is None:
            return

        elapsed = (self.get_clock().now() - self.last_motion_time).nanoseconds * 1e-9
        if elapsed > self.motion_timeout_sec:
            if self.last_cmd.linear.x != 0.0 or self.last_cmd.angular.z != 0.0:
                stop_cmd = Twist()
                self.cmd_vel_pub.publish(stop_cmd)
                self.last_cmd = stop_cmd
                self.last_motion_time = self.get_clock().now()
                self.get_logger().info('CMD_VEL watchdog: published stop after 1s timeout')


def main(args=None):
    rclpy.init(args=args)

    node = CommandNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
