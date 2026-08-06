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

        parts = text.split()
        cmd_word = parts[0]
        speed_val = 70.0
        if len(parts) > 1:
            try:
                speed_val = float(parts[1])
            except ValueError:
                pass

        if speed_val <= 100.0:
            scale = max(0.2, min(1.0, speed_val / 100.0))
        else:
            scale = max(0.2, min(1.0, speed_val / 255.0))

        v_lin = 0.60 * scale
        v_ang = 0.70 * scale

        # STOP
        if any(x in text for x in ['dừng', 'dung', 'stop', 'thôi', 'thoi', 'giu_nguyen']):
            self.publish_cmd(0.0, 0.0)

        # FORWARD
        elif any(x in text for x in ['đi thẳng', 'di thang', 'tiến', 'tien', 'forward', 'tiens_len']):
            self.publish_cmd(v_lin, 0.0)

        # BACKWARD
        elif any(x in text for x in ['đi lùi', 'di lui', 'lùi', 'lui', 'back', 'lui_lai']):
            self.publish_cmd(-v_lin, 0.0)

        # LEFT
        elif any(x in text for x in ['rẽ trái', 're trai', 'sang trái', 'quay_trai', 'left', 'trai']):
            self.publish_cmd(0.0, v_ang)

        # RIGHT
        elif any(x in text for x in ['rẽ phải', 're phai', 'sang phải', 'quay_phai', 'right', 'phai']):
            self.publish_cmd(0.0, -v_ang)

        # CHEO TRAI (DIAGONAL LEFT)
        elif any(x in text for x in ['chéo trái', 'cheo trai', 'tiến trái']):
            self.publish_cmd(v_lin * 0.75, v_ang * 0.75)

        # CHEO PHAI (DIAGONAL RIGHT)
        elif any(x in text for x in ['chéo phải', 'cheo phai', 'tiến phải']):
            self.publish_cmd(v_lin * 0.75, -v_ang * 0.75)

        # XOAY TRON (SPIN IN A CIRCLE)
        elif any(x in text for x in ['xoay tròn', 'xoay tron', 'vòng tròn', 'vong tron', 'quay 360', 'xoay 360', 'spin']):
            self.publish_cmd(0.0, 0.80 * scale)

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
