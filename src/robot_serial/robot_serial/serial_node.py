import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32, String, Float32MultiArray

from robot_serial.serial_manager import SerialManager
from robot_serial.sensor_parser import parse_sensor_line


def euler_to_quaternion(roll: float, pitch: float, yaw: float):
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
        return 'xoay_trai', speed
    if wz < -ANGULAR_SLOW_THRESHOLD:
        return 'xoay_phai', speed
    if vx > LINEAR_SLOW_THRESHOLD and vy > LINEAR_SLOW_THRESHOLD:
        return 'cheo_tt', speed
    if vx > LINEAR_SLOW_THRESHOLD and vy < -LINEAR_SLOW_THRESHOLD:
        return 'cheo_tp', speed
    if vx < -LINEAR_SLOW_THRESHOLD and vy > LINEAR_SLOW_THRESHOLD:
        return 'cheo_st', speed
    if vx < -LINEAR_SLOW_THRESHOLD and vy < -LINEAR_SLOW_THRESHOLD:
        return 'cheo_sp', speed
    if vx > LINEAR_SLOW_THRESHOLD:
        return 'tien', speed
    if vx < -LINEAR_SLOW_THRESHOLD:
        return 'lui', speed
    if vy > LINEAR_SLOW_THRESHOLD:
        return 'trai', speed
    if vy < -LINEAR_SLOW_THRESHOLD:
        return 'phai', speed
    return 'dung', 0


class SerialNode(Node):
    def __init__(self):
        super().__init__('serial_node')
        self.declare_parameter('port', 'auto')
        self.declare_parameter('baudrate', 115200)

        port_param = str(self.get_parameter('port').value)
        baudrate_param = int(self.get_parameter('baudrate').value)

        self.serial_manager = SerialManager(
            on_data_received=self._on_data_received,
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected,
            port=port_param,
            baudrate=baudrate_param,
        )
        self.connected = False

        self.rx_publisher = self.create_publisher(String, '/esp32/serial_rx', 10)
        self.tx_subscriber = self.create_subscription(
            String,
            '/esp32/serial_tx',
            self._on_tx_command,
            10,
        )
        self.robot_move_subscriber = self.create_subscription(
            String,
            '/robot/move',
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
        self.encoder_values_publisher = self.create_publisher(Float32MultiArray, '/esp32/encoder_values', 10)

        self.timer = self.create_timer(0.1, self._timer_callback)
        self._telemetry_enabled = False
        self._front_dist = 999.0
        self._rear_dist = 999.0
        self.get_logger().info('Serial node initialized')

    def _on_connected(self, port: str):
        self.connected = True
        self.get_logger().info(f'Connected to {port}')
        self._telemetry_enabled = True

    def _on_disconnected(self):
        self.connected = False
        self._telemetry_enabled = False
        self.get_logger().warn('Serial disconnected.')

    def _on_data_received(self, data: str):
        self.get_logger().debug(f'[RX]\n{data}')
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
            
            # Convert Roll, Pitch, Yaw from degrees to radians -> Quaternions
            roll = float(parsed['imu'].get('roll', 0.0))
            pitch = float(parsed['imu'].get('pitch', 0.0))
            yaw = float(parsed['imu'].get('yaw', 0.0))
            
            qx, qy, qz, qw = euler_to_quaternion(
                math.radians(roll),
                math.radians(pitch),
                math.radians(yaw)
            )
            imu_msg.orientation.x = qx
            imu_msg.orientation.y = qy
            imu_msg.orientation.z = qz
            imu_msg.orientation.w = qw
            
            self.imu_publisher.publish(imu_msg)

        if parsed.get('distance'):
            if 'front' in parsed['distance']:
                self._front_dist = float(parsed['distance']['front'])
                front_msg = Float32()
                front_msg.data = self._front_dist
                self.front_distance_publisher.publish(front_msg)
            if 'rear' in parsed['distance']:
                self._rear_dist = float(parsed['distance']['rear'])
                rear_msg = Float32()
                rear_msg.data = self._rear_dist
                self.rear_distance_publisher.publish(rear_msg)

        if parsed.get('battery') is not None:
            battery_msg = Float32()
            battery_msg.data = float(parsed['battery'])
            self.battery_publisher.publish(battery_msg)

        if parsed.get('encoder_distance') is not None:
            enc_msg = Float32()
            enc_msg.data = float(parsed['encoder_distance'])
            self.encoder_distance_publisher.publish(enc_msg)

        if parsed.get('encoders') is not None:
            val_msg = Float32MultiArray()
            val_msg.data = [float(v) for v in parsed['encoders']]
            self.encoder_values_publisher.publish(val_msg)

    def _translate_command(self, text: str) -> str:
        raw = text.strip()
        if not raw:
            return ""

        # Chuẩn hóa chuỗi lệnh tiếng Việt thành dạng chuẩn
        vietnamese_map = {
            "đi thẳng": "tien 150",
            "đi lùi": "lui 150",
            "rẽ trái": "trai 150",
            "rẽ phải": "phai 150",
            "xoay trái": "xoay_trai 150",
            "xoay phải": "xoay_phai 150",
            "chéo trái": "cheo_tt 150",
            "chéo phải": "cheo_tp 150",
            "lùi chéo trái": "cheo_st 150",
            "lùi chéo phải": "cheo_sp 150",
            "dừng": "dung",
            "dừng lại": "dung"
        }
        if raw.lower() in vietnamese_map:
            return vietnamese_map[raw.lower()]
        
        parts = raw.split()
        cmd = parts[0].lower()
        speed = parts[1] if len(parts) > 1 else "150"

        if cmd in ["mode_manual", "mode_auto", "mode_ros", "mode_ros2"]:
            return f"mode_{cmd.replace('mode_', '')}"
        if cmd.startswith("mode"):
            return raw

        translation_map = {
            "tien": "tien",
            "forward": "tien",
            "di_thang": "tien",
            "w": "tien",
            "lui": "lui",
            "backward": "lui",
            "di_lui": "lui",
            "s": "lui",
            "trai": "trai",
            "left": "trai",
            "strafe_left": "trai",
            "a": "trai",
            "phai": "phai",
            "right": "phai",
            "strafe_right": "phai",
            "d": "phai",
            "xoay_trai": "xoay_trai",
            "rotate_left": "xoay_trai",
            "q": "xoay_trai",
            "xoay_phai": "xoay_phai",
            "rotate_right": "xoay_phai",
            "e": "xoay_phai",
            "cheo_tt": "cheo_tt",
            "cheo_trai": "cheo_tt",
            "diag_fl": "cheo_tt",
            "diagonal_front_left": "cheo_tt",
            "z": "cheo_tt",
            "cheo_tp": "cheo_tp",
            "cheo_phai": "cheo_tp",
            "diag_fr": "cheo_tp",
            "diagonal_front_right": "cheo_tp",
            "c": "cheo_tp",
            "cheo_st": "cheo_st",
            "diagonal_rear_left": "cheo_st",
            "cheo_sp": "cheo_sp",
            "diagonal_rear_right": "cheo_sp",
            "dung": "dung",
            "stop": "dung",
            "x": "dung",
        }

        if cmd in translation_map:
            target = translation_map[cmd]
            if target == "dung":
                return "dung"
            return f"{target} {speed}"

        return raw

    def _on_tx_command(self, msg: String):
        if not self.connected:
            self.get_logger().warn('Cannot send command: serial not connected')
            return
        raw = msg.data.strip()
        if not raw:
            return
        payload = self._translate_command(raw)
        self.get_logger().info(f'[TX] {payload} (raw: "{raw}")')
        self.serial_manager.write_line(payload)

    def _on_cmd_vel(self, msg: Twist):
        if not self.connected:
            return
        linear_x = float(msg.linear.x)
        linear_y = float(msg.linear.y)
        angular_z = float(msg.angular.z)

        # Determine relevant obstacle distance based on direction
        dist = 999.0
        is_forward = False
        is_backward = False
        if linear_x > 0.0:
            dist = self._front_dist
            is_forward = True
        elif linear_x < 0.0:
            dist = self._rear_dist
            is_backward = True

        # Calculate speed factor based on valid obstacle distance (Ignore 0.0 disconnected sensor)
        speed_factor = 1.0
        if 0.1 <= dist <= 5.0:
            speed_factor = 0.0
        elif 5.0 < dist <= 20.0:
            speed_factor = 0.3
        elif 20.0 < dist <= 50.0:
            speed_factor = 0.6

        # Build command payload
        if speed_factor == 0.0:
            direction_name = "Front" if is_forward else "Rear"
            self.get_logger().warn(f"Safety Stop! {direction_name} obstacle too close: {dist:.1f} cm")
            payload = 'STOP'
        else:
            direction, speed = _speed_from_twist(linear_x, linear_y, angular_z)
            if speed <= 0 or direction == 'STOP':
                payload = 'STOP'
            else:
                # Apply speed factor and ensure minimum motor power (120) to overcome friction
                adjusted_speed = int(speed * speed_factor)
                adjusted_speed = max(120, min(adjusted_speed, 255))
                
                if speed_factor < 1.0:
                    direction_name = "Front" if is_forward else "Rear"
                    self.get_logger().info(
                        f"Safety slowdown ({int(speed_factor * 100)}%): "
                        f"{direction_name} obstacle at {dist:.1f} cm (Speed: {speed} -> {adjusted_speed})"
                    )
                
                payload = f'{direction} {adjusted_speed}'

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
                    err_msg = self.serial_manager.last_error or 'Serial device not found.'
                    self.get_logger().error(f'Connection failed: {err_msg}')
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