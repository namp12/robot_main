import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32, String

from robot_serial.serial_manager import SerialManager
from robot_serial.sensor_parser import parse_sensor_line


MAX_SPEED = 255
LINEAR_SLOW_THRESHOLD = 0.05
ANGULAR_SLOW_THRESHOLD = 0.2


def _speed_from_twist(vx: float, vy: float, wz: float) -> tuple[str, int]:
    speed = 0
    if vx > LINEAR_SLOW_THRESHOLD:
        speed = int(vx * 255)
    elif vx < -LINEAR_SLOW_THRESHOLD:
        speed = int(abs(vx) * 255)
    elif vy > LINEAR_SLOW_THRESHOLD:
        speed = int(vy * 255)
    elif vy < -LINEAR_SLOW_THRESHOLD:
        speed = int(abs(vy) * 255)
    elif abs(wz) > ANGULAR_SLOW_THRESHOLD:
        speed = int(abs(wz) * 200)

    speed = max(50, min(speed, MAX_SPEED))

    if abs(vx) < LINEAR_SLOW_THRESHOLD and abs(vy) < LINEAR_SLOW_THRESHOLD and abs(wz) < ANGULAR_SLOW_THRESHOLD:
        return 'dung', 0
    if wz > ANGULAR_SLOW_THRESHOLD:
        return 'xoay_phai', speed
    if wz < -ANGULAR_SLOW_THRESHOLD:
        return 'xoay_trai', speed
    if vx > LINEAR_SLOW_THRESHOLD and vy > LINEAR_SLOW_THRESHOLD:
        return 'cheo_tp', speed
    if vx > LINEAR_SLOW_THRESHOLD and vy < -LINEAR_SLOW_THRESHOLD:
        return 'cheo_tt', speed
    if vx < -LINEAR_SLOW_THRESHOLD and vy > LINEAR_SLOW_THRESHOLD:
        return 'cheo_sp', speed
    if vx < -LINEAR_SLOW_THRESHOLD and vy < -LINEAR_SLOW_THRESHOLD:
        return 'cheo_st', speed
    if vx > LINEAR_SLOW_THRESHOLD:
        return 'tien', speed
    if vx < -LINEAR_SLOW_THRESHOLD:
        return 'lui', speed
    if vy > LINEAR_SLOW_THRESHOLD:
        return 'phai', speed
    if vy < -LINEAR_SLOW_THRESHOLD:
        return 'trai', speed
    return 'dung', 0


class SerialNode(Node):
    def __init__(self):
        super().__init__('serial_node')
        self.serial_manager = SerialManager(
            on_data_received=self._on_data_received,
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected,
        )
        self.connected = False

        self.rx_publisher = self.create_publisher(String, '/esp32/serial_rx', 10)
        self.tx_subscriber = self.create_subscription(
            String,
            '/esp32/serial_tx',
            self._on_tx_command,
            10,
        )
        self.cmd_vel_subscriber = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._on_cmd_vel,
            10,
        )
        self.imu_publisher = self.create_publisher(Imu, '/imu/data', 10)
        self.front_distance_publisher = self.create_publisher(Float32, '/sensor/front_distance', 10)
        self.rear_distance_publisher = self.create_publisher(Float32, '/sensor/rear_distance', 10)
        self.battery_publisher = self.create_publisher(Float32, '/sensor/battery', 10)
        self.mode_publisher = self.create_publisher(String, '/esp32/mode', 10)
        self.status_publisher = self.create_publisher(String, '/esp32/status', 10)
        self.encoder_distance_publisher = self.create_publisher(Float32, '/esp32/encoder_distance', 10)

        self.timer = self.create_timer(0.1, self._timer_callback)
        self._telemetry_enabled = False
        self.get_logger().info('Serial node initialized')

    def _on_connected(self, port: str):
        self.connected = True
        self.get_logger().info(f'Connected to {port}')
        self._telemetry_enabled = True
        self.serial_manager.write_line('t on')

    def _on_disconnected(self):
        self.connected = False
        self._telemetry_enabled = False
        self.get_logger().warn('Serial disconnected.')

    def _on_data_received(self, data: str):
        self.get_logger().info(f'[RX]\n{data}')
        msg = String()
        msg.data = data
        self.rx_publisher.publish(msg)

        parsed = parse_sensor_line(data)
        if parsed.get('mode') is not None:
            mode_msg = String()
            mode_msg.data = str(parsed['mode'])
            self.mode_publisher.publish(mode_msg)

        if parsed.get('status') is not None:
            status_msg = String()
            status_msg.data = str(parsed['status'])
            self.status_publisher.publish(status_msg)

        if parsed.get('imu'):
            imu_msg = Imu()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = 'imu_link'
            imu_msg.linear_acceleration.x = float(parsed['imu'].get('ax', 0.0))
            imu_msg.linear_acceleration.y = float(parsed['imu'].get('ay', 0.0))
            imu_msg.linear_acceleration.z = float(parsed['imu'].get('az', 0.0))
            imu_msg.angular_velocity.x = float(parsed['imu'].get('gx', 0.0))
            imu_msg.angular_velocity.y = float(parsed['imu'].get('gy', 0.0))
            imu_msg.angular_velocity.z = float(parsed['imu'].get('gz', 0.0))
            self.imu_publisher.publish(imu_msg)

        if parsed.get('distance'):
            if 'front' in parsed['distance']:
                front_msg = Float32()
                front_msg.data = float(parsed['distance']['front'])
                self.front_distance_publisher.publish(front_msg)
            if 'rear' in parsed['distance']:
                rear_msg = Float32()
                rear_msg.data = float(parsed['distance']['rear'])
                self.rear_distance_publisher.publish(rear_msg)

        if parsed.get('battery') is not None:
            battery_msg = Float32()
            battery_msg.data = float(parsed['battery'])
            self.battery_publisher.publish(battery_msg)

        if parsed.get('encoder_distance') is not None:
            enc_msg = Float32()
            enc_msg.data = float(parsed['encoder_distance'])
            self.encoder_distance_publisher.publish(enc_msg)

    def _on_tx_command(self, msg: String):
        if not self.connected:
            self.get_logger().warn('Cannot send command: serial not connected')
            return
        payload = msg.data.strip()
        if not payload:
            return
        self.get_logger().info(f'[TX] {payload}')
        self.serial_manager.write_line(payload)

    def _on_cmd_vel(self, msg: Twist):
        if not self.connected:
            return
        direction, speed = _speed_from_twist(
            float(msg.linear.x),
            float(msg.linear.y),
            float(msg.angular.z),
        )
        if speed <= 0:
            payload = 'dung'
        else:
            payload = f'{direction} {speed}'
        self.serial_manager.write_line(payload)

    def _timer_callback(self):
        if not self.connected:
            if self.serial_manager.connect():
                pass
            else:
                if not hasattr(self, '_retry_count'):
                    self._retry_count = 0
                self._retry_count += 1
                if self._retry_count >= 20:
                    self.get_logger().error('Serial device not found.')
                    self._retry_count = 0
        else:
            while True:
                line = self.serial_manager.read_line()
                if line is None:
                    break


def main(args=None):
    rclpy.init(args=args)
    node = SerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.serial_manager.disconnect()
        except Exception:
            pass
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()