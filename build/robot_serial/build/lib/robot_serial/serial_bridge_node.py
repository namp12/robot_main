#!/usr/bin/env python3
"""
serial_bridge_node.py - ROS2 bridge between ESP32 and ROS2 topics.

This node is the sole communication link between Raspberry Pi and ESP32
connected via USB CDC Serial (/dev/ttyACM0).

Responsibilities:
  - Open and manage serial connection to ESP32
  - Read serial data (non-blocking)
  - Parse data using SerialParser
  - Publish parsed data to ROS2 topics
  - Subscribe to /cmd_vel and send commands to ESP32
  - Auto-reconnect if USB is disconnected

Architecture:
  ESP32 --[serial]--> SerialParser --> ROS2 Publishers
  ROS2 Subscriber --> SerialProtocol --[serial]--> ESP32

Published Topics:
  /wheel_encoder    (std_msgs/Int32MultiArray)  - [left, right] encoder ticks
  /imu_raw          (sensor_msgs/Imu)            - Raw IMU acceleration
  /battery_voltage  (std_msgs/Float32)           - Battery voltage
  /wheel_rpm        (std_msgs/Int32MultiArray)   - [left, right] wheel RPM
  /robot_status     (std_msgs/String)            - Robot status from ESP

Subscribed Topics:
  /cmd_vel          (geometry_msgs/Twist)        - Velocity commands

Parameters:
  port               (string) : Serial port (default: /dev/ttyACM0)
  baudrate           (int)    : Baud rate (default: 115200)
  timeout            (float)  : Serial read timeout (default: 0.1)
  reconnect_interval (float)  : Seconds between reconnect attempts (default: 3.0)
  frame_id           (string) : TF frame for IMU messages (default: base_link)

Author: robot
License: Apache-2.0
"""

import time
from typing import Optional

import serial
from serial import SerialException

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Float32, String
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist

from .serial_parser import SerialParser
from .serial_protocol import SerialProtocol


class RobotSerialNode(Node):
    """
    ROS2 node that bridges ESP32 serial communication to ROS2 topics.

    Features:
      - Non-blocking serial reads via timer callback
      - Auto-reconnect on USB disconnect
      - Exception handling that never crashes the node
      - Clean shutdown with proper serial release
    """

    def __init__(self) -> None:
        super().__init__('robot_serial_node')

        # ---- Declare ROS2 parameters ----
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('timeout', 0.1)
        self.declare_parameter('reconnect_interval', 3.0)
        self.declare_parameter('frame_id', 'base_link')

        # ---- Read parameters ----
        self._port: str = self.get_parameter('port').value
        self._baudrate: int = self.get_parameter('baudrate').value
        self._timeout: float = self.get_parameter('timeout').value
        self._reconnect_interval: float = self.get_parameter('reconnect_interval').value
        self._frame_id: str = self.get_parameter('frame_id').value

        # ---- Serial connection ----
        self._serial: Optional[serial.Serial] = None
        self._connected: bool = False

        # ---- Parser and Protocol ----
        self._parser = SerialParser()

        # ---- Receive buffer (accumulate partial lines) ----
        self._rx_buffer: str = ''

        # ---- Publishers ----
        self._encoder_pub = self.create_publisher(Int32MultiArray, '/wheel_encoder', 10)
        self._imu_pub = self.create_publisher(Imu, '/imu_raw', 10)
        self._battery_pub = self.create_publisher(Float32, '/battery_voltage', 10)
        self._rpm_pub = self.create_publisher(Int32MultiArray, '/wheel_rpm', 10)
        self._status_pub = self.create_publisher(String, '/robot_status', 10)

        # ---- Subscriber ----
        self._cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._cmd_vel_callback,
            10
        )

        # ---- Read timer (non-blocking serial read at 50Hz) ----
        self._read_timer = self.create_timer(0.02, self._read_timer_callback)

        # ---- Reconnect timer (checks connection every N seconds) ----
        self._reconnect_timer = self.create_timer(
            self._reconnect_interval,
            self._reconnect_timer_callback
        )

        # ---- Log startup ----
        self.get_logger().info(
            f'Robot Serial Node initialized: port={self._port}, '
            f'baudrate={self._baudrate}, timeout={self._timeout}s'
        )

        # ---- Attempt initial connection ----
        self._connect_serial()

    def _connect_serial(self) -> bool:
        """
        Open serial connection to ESP32.

        Returns:
            bool: True if connected successfully, False otherwise.
        """
        if self._serial is not None and self._serial.is_open:
            return True

        try:
            self.get_logger().info(f'Connecting to ESP32 on {self._port}...')

            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._timeout
            )

            if self._serial.is_open:
                self._connected = True
                self._rx_buffer = ''
                self.get_logger().info(f'Connected to ESP32 on {self._port}')
                return True
            else:
                self.get_logger().error(f'Failed to open {self._port}')
                return False

        except SerialException as exc:
            self.get_logger().error(f'Serial connection failed: {exc}')
            self._serial = None
            self._connected = False
            return False

        except Exception as exc:
            self.get_logger().error(f'Unexpected error connecting: {exc}')
            self._serial = None
            self._connected = False
            return False

    def _disconnect_serial(self) -> None:
        """Close serial connection safely."""
        if self._serial is not None:
            try:
                if self._serial.is_open:
                    self._serial.close()
                    self.get_logger().warning('Disconnected from ESP32')
            except Exception as exc:
                self.get_logger().error(f'Error closing serial: {exc}')
            finally:
                self._serial = None
                self._connected = False

    def _reconnect_timer_callback(self) -> None:
        """Periodic check: reconnect if serial is disconnected."""
        if self._connected and self._serial is not None and self._serial.is_open:
            return

        self.get_logger().info('Reconnecting to ESP32...')
        self._disconnect_serial()
        self._connect_serial()

    def _read_timer_callback(self) -> None:
        """
        Timer callback (50Hz): read available serial data and process.

        This is non-blocking - only reads what's available in the buffer.
        """
        if not self._connected or self._serial is None:
            return

        try:
            # Check if serial port is still open
            if not self._serial.is_open:
                self.get_logger().warning('Serial port closed unexpectedly')
                self._connected = False
                return

            # Read available data (non-blocking due to timeout)
            if self._serial.in_waiting > 0:
                raw_data = self._serial.read(self._serial.in_waiting)

                try:
                    # Decode bytes to string
                    text = raw_data.decode('utf-8', errors='ignore')
                    self._rx_buffer += text

                    # Process complete lines
                    while '\n' in self._rx_buffer:
                        line, self._rx_buffer = self._rx_buffer.split('\n', 1)
                        self._process_line(line)

                except UnicodeDecodeError as exc:
                    self.get_logger().warning(f'Decode error: {exc}')

        except SerialException as exc:
            self.get_logger().error(f'Serial read error: {exc}')
            self._connected = False

        except Exception as exc:
            self.get_logger().error(f'Unexpected read error: {exc}')

    def _process_line(self, line: str) -> None:
        """
        Process a single complete line from serial.

        Args:
            line: Raw line string (without newline)
        """
        # Parse the line
        parsed = self._parser.parse(line)

        if parsed is None:
            # Invalid or unrecognized message - ignore silently
            return

        msg_type = parsed['type']
        values = parsed['values']

        # Debug log
        self.get_logger().debug(f'Receive: {line.strip()}')

        # Dispatch to appropriate handler
        try:
            if msg_type == 'ENC':
                self._handle_encoder(values)
            elif msg_type == 'IMU':
                self._handle_imu(values)
            elif msg_type == 'BAT':
                self._handle_battery(values)
            elif msg_type == 'RPM':
                self._handle_rpm(values)
            elif msg_type == 'STATUS':
                self._handle_status(values)
        except Exception as exc:
            self.get_logger().error(f'Error handling {msg_type}: {exc}')

    def _handle_encoder(self, values: list) -> None:
        """Publish encoder data."""
        msg = Int32MultiArray()
        msg.data = [int(values[0]), int(values[1])]
        self._encoder_pub.publish(msg)
        self.get_logger().debug(f'Encoder: {values[0]} {values[1]}')

    def _handle_imu(self, values: list) -> None:
        """Publish IMU data."""
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id

        # Linear acceleration (m/s^2)
        msg.linear_acceleration.x = float(values[0])
        msg.linear_acceleration.y = float(values[1])
        msg.linear_acceleration.z = float(values[2])

        # Set orientation and angular velocity to zero (not provided by ESP)
        msg.orientation.w = 1.0
        msg.angular_velocity.x = 0.0
        msg.angular_velocity.y = 0.0
        msg.angular_velocity.z = 0.0

        self._imu_pub.publish(msg)

    def _handle_battery(self, values: list) -> None:
        """Publish battery voltage."""
        msg = Float32()
        msg.data = float(values[0])
        self._battery_pub.publish(msg)
        self.get_logger().debug(f'Battery: {values[0]:.2f}V')

    def _handle_rpm(self, values: list) -> None:
        """Publish wheel RPM."""
        msg = Int32MultiArray()
        msg.data = [int(values[0]), int(values[1])]
        self._rpm_pub.publish(msg)

    def _handle_status(self, values: list) -> None:
        """Publish robot status."""
        msg = String()
        msg.data = str(values[0])
        self._status_pub.publish(msg)
        self.get_logger().info(f'Status: {values[0]}')

    def _cmd_vel_callback(self, msg: Twist) -> None:
        """
        Callback for /cmd_vel subscription.
        Converts Twist to serial command and sends to ESP32.
        """
        if not self._connected or self._serial is None:
            return

        try:
            linear = msg.linear.x
            angular = msg.angular.z

            # Build command using protocol
            cmd_str = SerialProtocol.build_cmd_vel(linear, angular)

            # Send to serial
            self._serial.write(cmd_str.encode('utf-8'))

            self.get_logger().debug(f'Send: {cmd_str.strip()}')

        except SerialException as exc:
            self.get_logger().error(f'Failed to send cmd_vel: {exc}')
            self._connected = False

        except Exception as exc:
            self.get_logger().error(f'Error sending cmd_vel: {exc}')

    def send_command(self, command: str) -> bool:
        """
        Send an arbitrary command string to ESP32.

        Args:
            command: Complete command string (including frame delimiters)

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self._connected or self._serial is None:
            self.get_logger().warning('Cannot send command: not connected')
            return False

        try:
            self._serial.write(command.encode('utf-8'))
            self.get_logger().debug(f'Sent command: {command.strip()}')
            return True
        except Exception as exc:
            self.get_logger().error(f'Failed to send command: {exc}')
            return False

    def send_stop(self) -> bool:
        """Send emergency stop command."""
        return self.send_command(SerialProtocol.build_stop())

    def send_reset(self) -> bool:
        """Send reset command to ESP32."""
        return self.send_command(SerialProtocol.build_reset())

    def send_led(self, state: bool) -> bool:
        """Send LED control command."""
        return self.send_command(SerialProtocol.build_led(state))

    def send_pid(self, kp: float, ki: float, kd: float) -> bool:
        """Send PID tuning command."""
        return self.send_command(SerialProtocol.build_pid(kp, ki, kd))

    def destroy_node(self) -> None:
        """Clean shutdown: close serial before destroying node."""
        self.get_logger().info('Shutting down robot serial node...')

        # Send stop command before disconnecting
        if self._connected:
            self.send_stop()

        # Close serial
        self._disconnect_serial()

        # Cancel timers
        if self._read_timer is not None:
            self._read_timer.cancel()
        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()

        self.get_logger().info('Robot serial node shut down complete.')
        super().destroy_node()


def main(args: Optional[list] = None) -> None:
    """Entry point: initialize ROS2, create node, spin, cleanup."""
    rclpy.init(args=args)
    node = None

    try:
        node = RobotSerialNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        rclpy.logging.get_logger('robot_serial').error(f'Fatal error: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
