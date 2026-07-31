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

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.get_logger().info('Robot command node ONLINE')

    def publish_cmd(self, linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_pub.publish(msg)

        self.get_logger().info(
            f'CMD_VEL: linear={linear:.2f}, angular={angular:.2f}'
        )

    def command_callback(self, msg):
        text = msg.data.strip().lower()

        if not text:
            return

        self.get_logger().info(f'COMMAND RECEIVED: {msg.data}')

        # STOP
        if any(x in text for x in ['dừng', 'dung', 'stop', 'thôi', 'thoi']):
            self.publish_cmd(0.0, 0.0)

        # FORWARD
        elif any(x in text for x in ['đi thẳng', 'di thang', 'tiến', 'tien', 'forward']):
            self.publish_cmd(0.20, 0.0)

        # BACKWARD
        elif any(x in text for x in ['đi lùi', 'di lui', 'lùi', 'lui', 'back']):
            self.publish_cmd(-0.20, 0.0)

        # LEFT
        elif any(x in text for x in ['rẽ trái', 're trai', 'sang trái', 'sang trai', 'left']):
            self.publish_cmd(0.0, 0.50)

        # RIGHT
        elif any(x in text for x in ['rẽ phải', 're phai', 'sang phải', 'sang phai', 'right']):
            self.publish_cmd(0.0, -0.50)

        else:
            self.get_logger().warn(f'UNKNOWN COMMAND: {msg.data}')
            self.publish_cmd(0.0, 0.0)


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
