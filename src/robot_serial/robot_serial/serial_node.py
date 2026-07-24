import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32, String

from robot_serial.serial_manager import SerialManager
from robot_serial.sensor_parser import parse_sensor_line


class SerialNode(Node):
    """ROS2 Node for serial communication with ESP32."""
    
    def __init__(self):
        super().__init__('serial_node')
        
        # Initialize SerialManager with callbacks
        self.serial_manager = SerialManager(
            on_data_received=self._on_data_received,
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected
        )
        
        self.connected = False

        self.rx_publisher = self.create_publisher(String, '/esp32/serial_rx', 10)
        self.tx_subscriber = self.create_subscription(
            String,
            '/esp32/serial_tx',
            self._on_tx_command,
            10,
        )
        self.imu_publisher = self.create_publisher(Imu, '/imu/data', 10)
        self.front_distance_publisher = self.create_publisher(Float32, '/sensor/front_distance', 10)
        self.rear_distance_publisher = self.create_publisher(Float32, '/sensor/rear_distance', 10)
        self.battery_publisher = self.create_publisher(Float32, '/sensor/battery', 10)
        
        # Timer for connection retry and reading
        self.timer = self.create_timer(0.1, self._timer_callback)
        
        self.get_logger().info('Serial node initialized')
    
    def _on_connected(self, port: str):
        """Called when serial connection is established."""
        self.connected = True
        self.get_logger().info(f'Connected to {port}')
    
    def _on_disconnected(self):
        """Called when serial connection is lost."""
        self.connected = False
        self.get_logger().warn('Serial disconnected.')
    
    def _on_data_received(self, data: str):
        """Called when data is received from serial port."""
        self.get_logger().info(f'[RX]\n{data}')
        msg = String()
        msg.data = data
        self.rx_publisher.publish(msg)

        parsed = parse_sensor_line(data)
        if parsed['imu']:
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

        if parsed['distance']:
            if 'front' in parsed['distance']:
                front_msg = Float32()
                front_msg.data = float(parsed['distance']['front'])
                self.front_distance_publisher.publish(front_msg)
            if 'rear' in parsed['distance']:
                rear_msg = Float32()
                rear_msg.data = float(parsed['distance']['rear'])
                self.rear_distance_publisher.publish(rear_msg)

        if parsed['battery'] is not None:
            battery_msg = Float32()
            battery_msg.data = float(parsed['battery'])
            self.battery_publisher.publish(battery_msg)

    def _on_tx_command(self, msg: String):
        """Forward a command from ROS2 topic to the ESP32 over serial."""
        if not self.connected:
            self.get_logger().warn('Cannot send command: serial not connected')
            return
        payload = msg.data.strip()
        if not payload:
            return
        self.get_logger().info(f'[TX] {payload}')
        self.serial_manager.write_line(payload)
    
    def _timer_callback(self):
        """Timer callback for connection and reading."""
        # If not connected, try to reconnect
        if not self.connected:
            if self.serial_manager.connect():
                # Connected successfully, will trigger _on_connected callback
                pass
            else:
                # Still no device found, retry in next callback (0.1s)
                # Log every 20 attempts (every 2 seconds)
                if not hasattr(self, '_retry_count'):
                    self._retry_count = 0
                
                self._retry_count += 1
                if self._retry_count >= 20:
                    self.get_logger().error('Serial device not found.')
                    self._retry_count = 0
        else:
            # Connected, read incoming data
            while True:
                line = self.serial_manager.read_line()
                if line is None:
                    break
                # Data logging is done in _on_data_received callback


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
