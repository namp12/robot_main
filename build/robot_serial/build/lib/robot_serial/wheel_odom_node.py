import math
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Int32MultiArray, Float32MultiArray
from sensor_msgs.msg import Imu
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
    """Mecanum-drive odometry from 4-wheel RPM values with differential fallback."""

    def __init__(self):
        super().__init__('wheel_odometry_node')

        self.declare_parameter('wheel_radius', 0.033)
        self.declare_parameter('wheel_separation', 0.30)  # track width (distance left-right)
        self.declare_parameter('wheel_base', 0.20)        # wheelbase (distance front-rear)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('rpm_filter_alpha', 0.5)
        self.declare_parameter('odom_smoothing_alpha', 0.7)
        self.declare_parameter('use_imu_heading_correction', True)
        self.declare_parameter('imu_heading_alpha', 0.9)

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.wheel_base = self.get_parameter('wheel_base').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.publish_tf = self.get_parameter('publish_tf').value
        self.rpm_filter_alpha = float(self.get_parameter('rpm_filter_alpha').value)
        self.odom_smoothing_alpha = float(self.get_parameter('odom_smoothing_alpha').value)
        self.use_imu_heading_correction = self.get_parameter('use_imu_heading_correction').value
        self.imu_heading_alpha = float(self.get_parameter('imu_heading_alpha').value)

        # 4 Mecanum wheels
        self._rpm_fl: float = 0.0
        self._rpm_fr: float = 0.0
        self._rpm_rl: float = 0.0
        self._rpm_rr: float = 0.0
        self._imu_has_data: bool = False
        self._imu_yaw: float = 0.0
        
        self._last_time = self.get_clock().now()

        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0

        self._odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self._tf_broadcaster = TransformBroadcaster(self)

        self._last_distance: Optional[float] = None
        self._current_distance: float = 0.0
        self._last_encoders: Optional[list[float]] = None
        self._current_encoders: list[float] = [0.0, 0.0, 0.0, 0.0]

        self.create_subscription(
            Float32,
            '/esp32/encoder_distance',
            self._encoder_distance_callback,
            10,
        )

        self.create_subscription(
            Float32MultiArray,
            '/esp32/encoder_values',
            self._encoder_values_callback,
            10,
        )

        if self.use_imu_heading_correction:
            self.create_subscription(
                Imu,
                '/imu/data',
                self._imu_callback,
                10,
            )

        self.create_timer(1.0 / float(self.publish_rate), self._publish_odometry)

        self.get_logger().info(
            'Mecanum odometry node initialized: '
            f'wheel_radius={self.wheel_radius:.3f}m, '
            f'wheel_separation={self.wheel_separation:.3f}m, '
            f'wheel_base={self.wheel_base:.3f}m, '
            f'odom_frame={self.odom_frame}, base_frame={self.base_frame}'
        )

    def _encoder_distance_callback(self, msg: Float32) -> None:
        distance = float(msg.data)
        if self._last_distance is None:
            self._last_distance = distance

        self._current_distance = distance

    def _encoder_values_callback(self, msg: Float32MultiArray) -> None:
        if len(msg.data) >= 4:
            if self._last_encoders is None:
                self._last_encoders = list(msg.data[:4])

            self._current_encoders = list(msg.data[:4])

    def _wheel_rpm_callback(self, msg: Int32MultiArray) -> None:
        # Legacy callback preserved for compatibility but not used by current ESP32 pipeline.
        return

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    @staticmethod
    def _quaternion_to_yaw(orientation) -> float:
        x = orientation.x
        y = orientation.y
        z = orientation.z
        w = orientation.w
        # yaw (z-axis rotation)
        return math.atan2(
            2.0 * (w * z + x * y),
            1.0 - 2.0 * (y * y + z * z)
        )

    def _publish_odometry(self) -> None:
        now = self.get_clock().now()
        dt = (now - self._last_time).nanoseconds * 1e-9
        if dt <= 0.0:
            return

        self._last_time = now

        if self._last_encoders is not None:
            # Mecanum kinematics forward calculation using the 4 wheel distances
            d_fl = self._current_encoders[0] - self._last_encoders[0]
            d_fr = self._current_encoders[1] - self._last_encoders[1]
            d_rl = self._current_encoders[2] - self._last_encoders[2]
            d_rr = self._current_encoders[3] - self._last_encoders[3]

            lx = self.wheel_base / 2.0
            ly = self.wheel_separation / 2.0

            linear_velocity_x = (d_fl + d_fr + d_rl + d_rr) / (4.0 * dt)
            linear_velocity_y = (-d_fl + d_fr + d_rl - d_rr) / (4.0 * dt)
            angular_velocity = (-d_fl + d_fr - d_rl + d_rr) / (4.0 * (lx + ly) * dt)

            self._last_encoders = list(self._current_encoders)
        elif self._last_distance is not None:
            # Use encoder distance as the current primary odometry source.
            # This assumes /esp32/encoder_distance is a cumulative distance in meters.
            distance_delta = self._current_distance - self._last_distance
            linear_velocity_x = distance_delta / dt
            linear_velocity_y = 0.0
            angular_velocity = 0.0
            self._last_distance = self._current_distance
        else:
            # Legacy RPM-based odometry path if RPM values are available.
            v_fl = self._rpm_fl * 2.0 * math.pi * self.wheel_radius / 60.0
            v_fr = self._rpm_fr * 2.0 * math.pi * self.wheel_radius / 60.0
            v_rl = self._rpm_rl * 2.0 * math.pi * self.wheel_radius / 60.0
            v_rr = self._rpm_rr * 2.0 * math.pi * self.wheel_radius / 60.0

            if not hasattr(self, '_smoothed_v_fl'):
                self._smoothed_v_fl = v_fl
                self._smoothed_v_fr = v_fr
                self._smoothed_v_rl = v_rl
                self._smoothed_v_rr = v_rr

            alpha = max(0.0, min(1.0, self.odom_smoothing_alpha))
            self._smoothed_v_fl = alpha * v_fl + (1.0 - alpha) * self._smoothed_v_fl
            self._smoothed_v_fr = alpha * v_fr + (1.0 - alpha) * self._smoothed_v_fr
            self._smoothed_v_rl = alpha * v_rl + (1.0 - alpha) * self._smoothed_v_rl
            self._smoothed_v_rr = alpha * v_rr + (1.0 - alpha) * self._smoothed_v_rr

            v_fl = self._smoothed_v_fl
            v_fr = self._smoothed_v_fr
            v_rl = self._smoothed_v_rl
            v_rr = self._smoothed_v_rr

            # Mecanum kinematics forward equations
            # vx = forward velocity, vy = lateral velocity, wz = angular velocity
            lx = self.wheel_base / 2.0
            ly = self.wheel_separation / 2.0

            linear_velocity_x = (v_fl + v_fr + v_rl + v_rr) / 4.0
            linear_velocity_y = (-v_fl + v_fr + v_rl - v_rr) / 4.0
            angular_velocity = (-v_fl + v_fr - v_rl + v_rr) / (4.0 * (lx + ly))

        # Position integration in world coordinate frame
        delta_x = (linear_velocity_x * math.cos(self._yaw) - linear_velocity_y * math.sin(self._yaw)) * dt
        delta_y = (linear_velocity_x * math.sin(self._yaw) + linear_velocity_y * math.cos(self._yaw)) * dt
        delta_yaw = angular_velocity * dt

        self._x += delta_x
        self._y += delta_y
        self._yaw = self._normalize_angle(self._yaw + delta_yaw)

        if self.use_imu_heading_correction and getattr(self, '_imu_has_data', False):
            # Softly correct absolute yaw using IMU orientation
            yaw_error = self._normalize_angle(self._imu_yaw - self._yaw)
            correction_alpha = max(0.0, min(1.0, self.imu_heading_alpha))
            self._yaw = self._normalize_angle(self._yaw + (1.0 - correction_alpha) * yaw_error)

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
        if self.publish_tf:
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
        odom_msg.pose.covariance = [
            1e-5, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 1e-5, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1e-5, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1e-5, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1e-5, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 1e-3
        ]

        odom_msg.twist.twist.linear.x = linear_velocity_x
        odom_msg.twist.twist.linear.y = linear_velocity_y
        odom_msg.twist.twist.linear.z = 0.0
        odom_msg.twist.twist.angular.x = 0.0
        odom_msg.twist.twist.angular.y = 0.0
        odom_msg.twist.twist.angular.z = angular_velocity
        odom_msg.twist.covariance = [
            1e-5, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 1e-5, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1e-5, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1e-5, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1e-5, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 1e-3
        ]

        self._odom_pub.publish(odom_msg)

    def _imu_callback(self, msg: Imu) -> None:
        self._imu_yaw = self._quaternion_to_yaw(msg.orientation)
        self._imu_has_data = True


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
