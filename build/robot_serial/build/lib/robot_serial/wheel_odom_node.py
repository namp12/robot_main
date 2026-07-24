import math
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


try:
    from tf_transformations import quaternion_from_euler
    HAS_TF_TRANSFORMS = True
except ImportError:
    HAS_TF_TRANSFORMS = False


def euler_to_quaternion(roll: float, pitch: float, yaw: float):
    if HAS_TF_TRANSFORMS:
        q = quaternion_from_euler(roll, pitch, yaw)
        return float(q[0]), float(q[1]), float(q[2]), float(q[3])

    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy
    qw = cr * cp * cy + sr * sp * sy

    return qx, qy, qz, qw


class WheelOdometryNode(Node):
    """Differential-drive odometry from wheel RPM values."""

    def __init__(self):
        super().__init__('wheel_odometry_node')

        self.declare_parameter('wheel_radius', 0.033)
        self.declare_parameter('wheel_separation', 0.30)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('publish_rate', 20.0)

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.publish_rate = self.get_parameter('publish_rate').value

        self._rpm_left: float = 0.0
        self._rpm_right: float = 0.0
        self._last_time = self.get_clock().now()

        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0

        self._odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self._tf_broadcaster = TransformBroadcaster(self)

        self.create_subscription(
            Int32MultiArray,
            '/wheel_rpm',
            self._wheel_rpm_callback,
            10,
        )

        self.create_timer(1.0 / float(self.publish_rate), self._publish_odometry)

        self.get_logger().info(
            'Wheel odometry node initialized: '
            f'wheel_radius={self.wheel_radius:.3f}m, '
            f'wheel_separation={self.wheel_separation:.3f}m, '
'
            f'odom_frame={self.odom_frame}, base_frame={self.base_frame}'
        )

    def _wheel_rpm_callback(self, msg: Int32MultiArray) -> None:
        if len(msg.data) < 2:
            return
        self._rpm_left = float(msg.data[0])
        self._rpm_right = float(msg.data[1])

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def _publish_odometry(self) -> None:
        now = self.get_clock().now()
        dt = (now - self._last_time).nanoseconds * 1e-9
        if dt <= 0.0:
            return

        self._last_time = now

        v_l = self._rpm_left * 2.0 * math.pi * self.wheel_radius / 60.0
        v_r = self._rpm_right * 2.0 * math.pi * self.wheel_radius / 60.0

        linear_velocity = 0.5 * (v_l + v_r)
        angular_velocity = (v_r - v_l) / self.wheel_separation

        delta_x = linear_velocity * dt * math.cos(self._yaw)
        delta_y = linear_velocity * dt * math.sin(self._yaw)
        delta_yaw = angular_velocity * dt

        self._x += delta_x
        self._y += delta_y
        self._yaw = self._normalize_angle(self._yaw + delta_yaw)

        # Publish odom -> base_footprint transform
        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, self._yaw)
        transform = TransformStamped()
        transform.header.stamp = now.to_msg()
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = self._x
        transform.transform.translation.y = self._y
        transform.transform.translation.z = 0.0
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        self._tf_broadcaster.sendTransform(transform)

        odom_msg = Odometry()
        odom_msg.header.stamp = now.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_frame
        odom_msg.pose.pose.position.x = self._x
        odom_msg.pose.pose.position.y = self._y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation.x = qx
        odom_msg.pose.pose.orientation.y = qy
        odom_msg.pose.pose.orientation.z = qz
        odom_msg.pose.pose.orientation.w = qw

        odom_msg.twist.twist.linear.x = linear_velocity
        odom_msg.twist.twist.linear.y = 0.0
        odom_msg.twist.twist.angular.z = angular_velocity

        self._odom_pub.publish(odom_msg)


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = WheelOdometryNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
