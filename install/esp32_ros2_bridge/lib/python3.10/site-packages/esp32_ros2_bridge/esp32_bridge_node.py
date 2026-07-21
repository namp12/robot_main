#!/usr/bin/env python3
"""
ESP32 ROS2 Bridge Node - Binary Protocol Implementation
Handles bidirectional communication with ESP32 via Serial

Protocol:
- Header: 0xFF 0xFE
- MsgID: 1 byte (0x01=TELEMETRY, 0x02=CMD_VEL, 0x03=SET_MODE, 0x04=RESET_YAW)
- Length: 1 byte
- Payload: N bytes
- CRC16: 2 bytes (MODBUS, little-endian)
- Tail: 0xFD
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

import serial
import struct
import time
from enum import Enum
from typing import Optional, Tuple

# ROS2 Message Types
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, Range
from std_msgs.msg import String
from tf_transformations import quaternion_from_euler


class MsgID(Enum):
    """Binary protocol message IDs."""
    TELEMETRY = 0x01  # ESP32 -> Pi (44 bytes)
    CMD_VEL = 0x02    # Pi -> ESP32 (12 bytes)
    SET_MODE = 0x03   # Pi -> ESP32 (2 bytes)
    RESET_YAW = 0x04  # Pi -> ESP32 (0 bytes)


class ParserState(Enum):
    """Serial parser state machine."""
    IDLE = 0
    HEADER_2 = 1
    MSG_ID = 2
    LENGTH = 3
    PAYLOAD = 4
    CRC_1 = 5
    CRC_2 = 6
    TAIL = 7


class BinaryProtocol:
    """Binary protocol encoder/decoder for ESP32 communication."""
    
    HEADER_1 = 0xFF
    HEADER_2 = 0xFE
    TAIL = 0xFD
    
    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """
        Calculate CRC16-MODBUS (polynomial 0xA001, initial 0xFFFF).
        
        Args:
            data: Bytes to calculate CRC for
            
        Returns:
            CRC16 value
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    @staticmethod
    def pack_frame(msg_id: int, payload: bytes) -> bytes:
        """
        Pack binary frame for transmission.
        
        Args:
            msg_id: Message ID (0x01, 0x02, 0x03, 0x04)
            payload: Payload bytes
            
        Returns:
            Complete frame bytes
        """
        length = len(payload)
        crc_data = struct.pack('BB', msg_id, length) + payload
        crc16 = BinaryProtocol.calculate_crc16(crc_data)
        
        frame = struct.pack('BB', BinaryProtocol.HEADER_1, BinaryProtocol.HEADER_2)
        frame += struct.pack('BB', msg_id, length)
        frame += payload
        frame += struct.pack('<H', crc16)  # Little-endian CRC16
        frame += struct.pack('B', BinaryProtocol.TAIL)
        
        return frame
    
    @staticmethod
    def unpack_telemetry(payload: bytes) -> Optional[dict]:
        """
        Unpack telemetry payload (MsgID 0x01, 44 bytes).
        
        Format: '<IffffffffffffBBhhhhB'
        - timestamp_ms (uint32)
        - accel_x, accel_y, accel_z (3x float32)
        - gyro_x, gyro_y, gyro_z (3x float32)
        - roll, pitch, yaw (3x float32)
        - front_distance, rear_distance (2x float32)
        - current_mode (uint8)
        - auto_state (uint8)
        - motor_fl_speed, motor_fr_speed, motor_rl_speed, motor_rr_speed (4x int16)
        - flags (uint8)
        
        Args:
            payload: 44-byte telemetry payload
            
        Returns:
            Decoded telemetry dict or None on error
        """
        if len(payload) != 44:
            return None
        
        try:
            data = struct.unpack('<IffffffffffffBBhhhhB', payload)
            
            return {
                'timestamp_ms': data[0],
                'accel_x': data[1],
                'accel_y': data[2],
                'accel_z': data[3],
                'gyro_x': data[4],
                'gyro_y': data[5],
                'gyro_z': data[6],
                'roll': data[7],
                'pitch': data[8],
                'yaw': data[9],
                'front_distance': data[10],
                'rear_distance': data[11],
                'current_mode': data[12],
                'auto_state': data[13],
                'motor_fl_speed': data[14],
                'motor_fr_speed': data[15],
                'motor_rl_speed': data[16],
                'motor_rr_speed': data[17],
                'flags': data[18],
            }
        except struct.error:
            return None


class SerialParser:
    """State machine parser for binary protocol over serial."""
    
    def __init__(self):
        self.state = ParserState.IDLE
        self.msg_id = 0
        self.length = 0
        self.payload = bytearray()
        self.crc16 = 0
        
    def feed_byte(self, byte: int) -> Optional[Tuple[int, bytes, int]]:
        """
        Feed a single byte to the state machine.
        
        Args:
            byte: Single byte value (0-255)
            
        Returns:
            Tuple of (msg_id, payload, crc16) when frame complete, None otherwise
        """
        if self.state == ParserState.IDLE:
            if byte == BinaryProtocol.HEADER_1:
                self.state = ParserState.HEADER_2
            return None
            
        elif self.state == ParserState.HEADER_2:
            if byte == BinaryProtocol.HEADER_2:
                self.state = ParserState.MSG_ID
            else:
                self.state = ParserState.IDLE
            return None
            
        elif self.state == ParserState.MSG_ID:
            self.msg_id = byte
            self.state = ParserState.LENGTH
            return None
            
        elif self.state == ParserState.LENGTH:
            self.length = byte
            self.payload = bytearray()
            if self.length == 0:
                self.state = ParserState.CRC_1
            else:
                self.state = ParserState.PAYLOAD
            return None
            
        elif self.state == ParserState.PAYLOAD:
            self.payload.append(byte)
            if len(self.payload) == self.length:
                self.state = ParserState.CRC_1
            return None
            
        elif self.state == ParserState.CRC_1:
            self.crc16 = byte
            self.state = ParserState.CRC_2
            return None
            
        elif self.state == ParserState.CRC_2:
            self.crc16 |= (byte << 8)
            self.state = ParserState.TAIL
            return None
            
        elif self.state == ParserState.TAIL:
            if byte == BinaryProtocol.TAIL:
                # Frame complete and valid tail
                result = (self.msg_id, bytes(self.payload), self.crc16)
                self.state = ParserState.IDLE
                return result
            else:
                # Invalid tail, reset
                self.state = ParserState.IDLE
                return None
        
        return None
    
    def reset(self):
        """Reset parser state."""
        self.state = ParserState.IDLE
        self.msg_id = 0
        self.length = 0
        self.payload = bytearray()
        self.crc16 = 0


class ESP32BridgeNode(Node):
    """ROS2 Node for ESP32 binary protocol communication."""
    
    def __init__(self):
        super().__init__('esp32_bridge_node')
        
        # Declare parameters
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        
        # Get parameter values
        self.port = self.get_parameter('port').value
        self.baudrate = self.get_parameter('baudrate').value
        
        # Serial connection
        self.serial = None
        self.connected = False
        
        # Parser
        self.parser = SerialParser()
        
        # Telemetry data
        self.telemetry = {}
        
        # Publishers
        self.pub_imu = self.create_publisher(Imu, '/imu/data_raw', 10)
        self.pub_range_front = self.create_publisher(Range, '/range/front', 10)
        self.pub_range_rear = self.create_publisher(Range, '/range/rear', 10)
        self.pub_status = self.create_publisher(String, '/esp32/status', 10)
        
        # Subscribers
        self.sub_cmd_vel = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._on_cmd_vel,
            10
        )
        
        # Timers
        self.timer_serial = self.create_timer(0.01, self._timer_serial_read)  # 100Hz
        self.timer_status = self.create_timer(1.0, self._timer_publish_status)  # 1Hz
        
        self.get_logger().info(f'ESP32 Bridge Node initialized')
        self.get_logger().info(f'Serial port: {self.port}, Baudrate: {self.baudrate}')
        
        # Connect and switch to ROS2 mode
        self._connect_serial()
        if self.connected:
            self._send_set_mode(target_mode=2, e_stop=0)  # MODE_ROS2
    
    def _connect_serial(self) -> bool:
        """Connect to serial port."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            self.connected = True
            self.get_logger().info(f'Connected to {self.port} at {self.baudrate} baud')
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to connect to {self.port}: {e}')
            self.connected = False
            return False
    
    def _disconnect_serial(self):
        """Disconnect from serial port."""
        if self.serial is not None:
            try:
                self.serial.close()
            except Exception:
                pass
        self.connected = False
    
    def _send_frame(self, msg_id: int, payload: bytes = b'') -> bool:
        """
        Send frame via serial.
        
        Args:
            msg_id: Message ID
            payload: Payload bytes
            
        Returns:
            True if sent successfully
        """
        if not self.connected or self.serial is None:
            return False
        
        try:
            frame = BinaryProtocol.pack_frame(msg_id, payload)
            self.serial.write(frame)
            self.serial.flush()
            return True
        except Exception as e:
            self.get_logger().warn(f'Failed to send frame: {e}')
            return False
    
    def _send_cmd_vel(self, linear_x: float, linear_y: float, angular_z: float) -> bool:
        """
        Send CMD_VEL command to ESP32.
        
        Args:
            linear_x: Linear velocity X (m/s)
            linear_y: Linear velocity Y (m/s)
            angular_z: Angular velocity Z (rad/s)
            
        Returns:
            True if sent successfully
        """
        payload = struct.pack('<fff', linear_x, linear_y, angular_z)
        return self._send_frame(MsgID.CMD_VEL.value, payload)
    
    def _send_set_mode(self, target_mode: int, e_stop: int) -> bool:
        """
        Send SET_MODE command to ESP32.
        
        Args:
            target_mode: Target mode (0=MANUAL, 1=AUTO, 2=ROS2)
            e_stop: Emergency stop flag (0=normal, 1=estop)
            
        Returns:
            True if sent successfully
        """
        payload = struct.pack('<BB', target_mode, e_stop)
        return self._send_frame(MsgID.SET_MODE.value, payload)
    
    def _send_reset_yaw(self) -> bool:
        """Send RESET_YAW command to ESP32."""
        return self._send_frame(MsgID.RESET_YAW.value, b'')
    
    def _on_cmd_vel(self, msg: Twist):
        """Handle /cmd_vel subscription."""
        self._send_cmd_vel(
            msg.linear.x,
            msg.linear.y,
            msg.angular.z
        )
    
    def _process_telemetry(self, payload: bytes):
        """
        Process telemetry frame from ESP32.
        
        Args:
            payload: 44-byte telemetry payload
        """
        self.telemetry = BinaryProtocol.unpack_telemetry(payload)
        if self.telemetry is None:
            self.get_logger().warn('Invalid telemetry payload')
            return
        
        # Publish IMU data
        self._publish_imu()
        
        # Publish range data
        self._publish_range()
    
    def _publish_imu(self):
        """Publish IMU data as /imu/data_raw."""
        if not self.telemetry:
            return
        
        msg = Imu()
        
        # Timestamp
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'
        
        # Linear acceleration (m/s^2)
        msg.linear_acceleration.x = self.telemetry['accel_x']
        msg.linear_acceleration.y = self.telemetry['accel_y']
        msg.linear_acceleration.z = self.telemetry['accel_z']
        
        # Angular velocity (rad/s)
        msg.angular_velocity.x = self.telemetry['gyro_x']
        msg.angular_velocity.y = self.telemetry['gyro_y']
        msg.angular_velocity.z = self.telemetry['gyro_z']
        
        # Orientation from roll, pitch, yaw (convert degrees to radians)
        roll = self.telemetry['roll'] * 3.14159265359 / 180.0
        pitch = self.telemetry['pitch'] * 3.14159265359 / 180.0
        yaw = self.telemetry['yaw'] * 3.14159265359 / 180.0
        
        quat = quaternion_from_euler(roll, pitch, yaw)
        msg.orientation.x = quat[0]
        msg.orientation.y = quat[1]
        msg.orientation.z = quat[2]
        msg.orientation.w = quat[3]
        
        self.pub_imu.publish(msg)
    
    def _publish_range(self):
        """Publish range data as /range/front and /range/rear."""
        if not self.telemetry:
            return
        
        # Front range
        msg_front = Range()
        msg_front.header.stamp = self.get_clock().now().to_msg()
        msg_front.header.frame_id = 'front_sensor'
        msg_front.radiation_type = Range.ULTRASOUND
        msg_front.field_of_view = 0.26  # radians
        msg_front.min_range = 0.02
        msg_front.max_range = 4.0
        msg_front.range = self.telemetry['front_distance'] / 100.0  # cm to m
        
        self.pub_range_front.publish(msg_front)
        
        # Rear range
        msg_rear = Range()
        msg_rear.header.stamp = self.get_clock().now().to_msg()
        msg_rear.header.frame_id = 'rear_sensor'
        msg_rear.radiation_type = Range.ULTRASOUND
        msg_rear.field_of_view = 0.26  # radians
        msg_rear.min_range = 0.02
        msg_rear.max_range = 4.0
        msg_rear.range = self.telemetry['rear_distance'] / 100.0  # cm to m
        
        self.pub_range_rear.publish(msg_rear)
    
    def _timer_serial_read(self):
        """Timer callback for serial reading (100Hz)."""
        if not self.connected or self.serial is None:
            return
        
        try:
            while self.serial.in_waiting > 0:
                byte = self.serial.read(1)
                if not byte:
                    break
                
                result = self.parser.feed_byte(byte[0])
                
                if result is not None:
                    msg_id, payload, crc16 = result
                    
                    # Verify CRC16
                    crc_data = struct.pack('BB', msg_id, len(payload)) + payload
                    expected_crc = BinaryProtocol.calculate_crc16(crc_data)
                    
                    if crc16 != expected_crc:
                        self.get_logger().warn(
                            f'CRC mismatch: expected {expected_crc:04x}, got {crc16:04x}'
                        )
                        continue
                    
                    # Process message
                    if msg_id == MsgID.TELEMETRY.value:
                        self._process_telemetry(payload)
                    else:
                        self.get_logger().debug(f'Received message ID: {msg_id}')
        
        except serial.SerialException as e:
            self.get_logger().error(f'Serial error: {e}')
            self.connected = False
        except Exception as e:
            self.get_logger().error(f'Unexpected error in serial read: {e}')
    
    def _timer_publish_status(self):
        """Timer callback for publishing status (1Hz)."""
        if not self.telemetry:
            msg = String()
            msg.data = 'Waiting for ESP32 telemetry...'
            self.pub_status.publish(msg)
            return
        
        # Parse status from telemetry
        mode_names = {0: 'MANUAL', 1: 'AUTO', 2: 'ROS2'}
        mode = mode_names.get(self.telemetry['current_mode'], 'UNKNOWN')
        
        flags = self.telemetry['flags']
        mpu_ok = bool(flags & 0x01)
        front_online = bool(flags & 0x02)
        rear_online = bool(flags & 0x04)
        e_stop = bool(flags & 0x08)
        
        status_str = (
            f"Mode: {mode} | "
            f"MPU: {'OK' if mpu_ok else 'FAIL'} | "
            f"Front: {'OK' if front_online else 'OFFLINE'} | "
            f"Rear: {'OK' if rear_online else 'OFFLINE'} | "
            f"EStop: {'ACTIVE' if e_stop else 'NORMAL'} | "
            f"Motors: FL={self.telemetry['motor_fl_speed']} "
            f"FR={self.telemetry['motor_fr_speed']} "
            f"RL={self.telemetry['motor_rl_speed']} "
            f"RR={self.telemetry['motor_rr_speed']}"
        )
        
        msg = String()
        msg.data = status_str
        self.pub_status.publish(msg)
    
    def destroy_node(self):
        """Clean shutdown."""
        self.get_logger().info('Shutting down ESP32 Bridge Node')
        
        # Send MANUAL mode with estop before shutdown
        if self.connected:
            self._send_set_mode(target_mode=0, e_stop=1)
            time.sleep(0.1)
        
        self._disconnect_serial()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ESP32BridgeNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
