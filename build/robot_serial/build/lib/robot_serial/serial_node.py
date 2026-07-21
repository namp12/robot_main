import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
import time

from robot_serial.serial_manager import SerialManager


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
        node.serial_manager.disconnect()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
