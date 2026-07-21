#!/usr/bin/env python3
"""
ESP32 ROS2 Bridge Node - Binary Protocol Implementation
ROS2 Humble Package: esp32_ros2_bridge
Runs on Raspberry Pi 4 (Ubuntu 22.04), communicates 2-way with ESP32 via Serial.

Protocol Specification:
- Header: 2 Bytes [0xFF, 0xFE]
- MsgID: 1 Byte
  - 0x01: TELEMETRY (ESP32 -> Pi, 50Hz)
  - 0x02: CMD_VEL   (Pi -> ESP32)
  - 0x03: SET_MODE  (Pi -> ESP32)
  - 0x04: RESET_YAW (Pi -> ESP32)
- Length: 1 Byte (N)
- Payload: N Bytes
- CRC16: 2 Bytes (CRC16-MODBUS/CCITT, Little-Endian uint16 over [MsgID + Length + Payload])
- Tail: 1 Byte [0xFD]
"""

import math
import struct
import time
from enum import Enum
from typing import Optional, Tuple, Dict, Any

import rclpy
from rclpy.node import Node

import serial

# ROS2 Message Types
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, Range
from std_msgs.msg import String

# Try importing tf_transformations, fallback to pure math if unavailable
try:
    from tf_transformations import quaternion_from_euler
    HAS_TF_TRANSFORMS = True
except ImportError:
    HAS_TF_TRANSFORMS = False


def calculate_crc16(data: bytes) -> int:
    """
    Calculate CRC16-MODBUS (polynomial 0xA001, initial 0xFFFF).
    
    Args:
        data: Bytes to calculate CRC for ([MsgID + Length + Payload])
        
    Returns:
        16-bit unsigned integer CRC
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


def euler_to_quaternion(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    """
    Convert Euler angles (roll, pitch, yaw in radians) to Quaternion (x, y, z, w).
    """
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


class MsgID(Enum):
    """Binary protocol message IDs."""
    TELEMETRY = 0x01  # ESP32 -> Pi
    CMD_VEL = 0x02    # Pi -> ESP32
    SET_MODE = 0x03   # Pi -> ESP32
    RESET_YAW = 0x04  # Pi -> ESP32


class ParserState(Enum):
    """Byte-by-byte parser state machine."""
    IDLE = 0
    HEADER_2 = 1
    MSG_ID = 2
    LENGTH = 3
    PAYLOAD = 4
    CRC_1 = 5
    CRC_2 = 6
    TAIL = 7


class BinaryProtocol:
    """Encoder and Decoder for Binary Frame Protocol."""
    
    HEADER_1 = 0xFF
    HEADER_2 = 0xFE
    TAIL = 0xFD
    
    # Format strings for 11 floats (59 bytes) and 12 floats (63 bytes)
    FMT_TELEMETRY_59 = '<IfffffffffffBBhhhhB'   # 11 floats: accel(3)+gyro(3)+r/p/y(3)+dist(2)
    FMT_TELEMETRY_63 = '<IffffffffffffBBhhhhB'  # 12 floats variant
    
    @staticmethod
    def pack_frame(msg_id: int, payload: bytes) -> bytes:
        """
        Pack binary frame for serial transmission.
        
        Frame layout: [Header1, Header2, MsgID, Length, Payload, CRC16_L, CRC16_H, Tail]
        CRC calculated over: [MsgID + Length + Payload]
        """
        length = len(payload)
        crc_data = struct.pack('BB', msg_id, length) + payload
        crc16 = calculate_crc16(crc_data)
        
        frame = bytearray()
        frame.append(BinaryProtocol.HEADER_1)
        frame.append(BinaryProtocol.HEADER_2)
        frame.append(msg_id)
        frame.append(length)
        frame.extend(payload)
        frame.extend(struct.pack('<H', crc16))  # Little-Endian uint16
        frame.append(BinaryProtocol.TAIL)
        return bytes(frame)
    
    @staticmethod
    def unpack_telemetry(payload: bytes) -> Optional[Dict[str, Any]]:
        """
        Unpack Telemetry Payload (MsgID 0x01).
        
        Fields:
        1. timestamp_ms (uint32)
        2. accel_x, accel_y, accel_z (3x float32)
        3. gyro_x, gyro_y, gyro_z (3x float32)
        4. roll, pitch, yaw (3x float32 - degrees)
        5. front_distance, rear_distance (2x float32 - cm)
        6. current_mode (uint8: 0=MANUAL, 1=AUTO, 2=ROS2)
        7. auto_state (uint8)
        8. motor_fl_speed, motor_fr_speed, motor_rl_speed, motor_rr_speed (4x int16)
        9. flags (uint8: Bit 0=mpuOk, Bit 1=frontOnline, Bit 2=rearOnline, Bit 3=eStop)
        """
        payload_len = len(payload)
        
        if payload_len == 59 or payload_len == 44:
            fmt = BinaryProtocol.FMT_TELEMETRY_59
        elif payload_len == 63:
            fmt = BinaryProtocol.FMT_TELEMETRY_63
        else:
            # Fallback format matching expected 11 floats struct
            fmt = BinaryProtocol.FMT_TELEMETRY_59
        
        try:
            data = struct.unpack(fmt, payload)
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
        except Exception:
            return None


class SerialParser:
    """Byte-by-byte state machine parser for serial streams."""
    
    def __init__(self):
        self.state = ParserState.IDLE
        self.msg_id = 0
        self.length = 0
        self.payload = bytearray()
        self.crc16 = 0
        
    def feed_byte(self, byte: int) -> Optional[Tuple[int, bytes, int]]:
        """
        Feed a single byte into the state machine parser.
        Returns (msg_id, payload, crc16) when a complete frame is parsed, otherwise None.
        """
        if self.state == ParserState.IDLE:
            if byte == BinaryProtocol.HEADER_1:
                self.state = ParserState.HEADER_2
            return None

        elif self.state == ParserState.HEADER_2:
            if byte == BinaryProtocol.HEADER_2:
                self.state = ParserState.MSG_ID
            else:
                self.state = ParserState.IDLE if byte != BinaryProtocol.HEADER_1 else ParserState.HEADER_2
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
            current_msg_id = self.msg_id
            current_payload = bytes(self.payload)
            current_crc = self.crc16
            
            self.state = ParserState.IDLE
            if byte == BinaryProtocol.TAIL:
                return (current_msg_id, current_payload, current_crc)
            return None

        self.state = ParserState.IDLE
        return None

    def reset(self):
        """Reset state machine parser."""
        self.state = ParserState.IDLE
        self.msg_id = 0
        self.length = 0
        self.payload = bytearray()
        self.crc16 = 0


class ESP32BridgeNode(Node):
    """ROS2 Humble Node communicating bidirectionally with ESP32 via Serial."""
    
    def __init__(self):
        super().__init__('esp32_bridge_node')
        
        # Declare parameters
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        
        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        
        self.serial_port = None
        self.is_connected = False
        self.parser = SerialParser()
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        
        # ROS2 Publishers
        self.pub_imu = self.create_publisher(Imu, '/imu/data_raw', 10)
        self.pub_range_front = self.create_publisher(Range, '/range/front', 10)
        self.pub_range_rear = self.create_publisher(Range, '/range/rear', 10)
        self.pub_status = self.create_publisher(String, '/esp32/status', 10)
        
        # ROS2 Subscribers
        self.sub_cmd_vel = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._cmd_vel_callback,
            10
        )
        
        # 100Hz Non-blocking Serial Timer (0.01 seconds)
        self.timer_serial = self.create_timer(0.01, self._timer_serial_read_callback)
        
        # 1Hz Status Publisher Timer
        self.timer_status = self.create_timer(1.0, self._timer_status_callback)
        
        self.get_logger().info(f'ESP32 ROS2 Bridge initialized on port={self.port}, baud={self.baudrate}')
        
        # Connect to Serial Port
        self._connect_serial()
        
        # Auto-Switch Mode to MODE_ROS2 (target_mode=2, e_stop=0) on startup
        if self.is_connected:
            self._send_set_mode(target_mode=2, e_stop=0)
            self.get_logger().info('Sent SET_MODE command: target_mode=2 (ROS2), e_stop=0')

    def _connect_serial(self) -> bool:
        """Establish serial connection to ESP32."""
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.0,
                write_timeout=0.1
            )
            self.is_connected = True
            self.get_logger().info(f'Successfully connected to serial port {self.port}')
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to open serial port {self.port}: {e}')
            self.is_connected = False
            return False

    def _send_raw_frame(self, msg_id: int, payload: bytes = b'') -> bool:
        """Pack frame with CRC16 and send to ESP32."""
        if not self.is_connected or self.serial_port is None:
            return False
        
        try:
            frame = BinaryProtocol.pack_frame(msg_id, payload)
            self.serial_port.write(frame)
            self.serial_port.flush()
            return True
        except Exception as e:
            self.get_logger().warn(f'Serial write failed: {e}')
            return False

    def _send_set_mode(self, target_mode: int, e_stop: int) -> bool:
        """
        Send MsgID 0x03 SET_MODE command.
        Payload format: '<BB' (2 Bytes)
        """
        payload = struct.pack('<BB', target_mode, e_stop)
        return self._send_raw_frame(MsgID.SET_MODE.value, payload)

    def _send_reset_yaw(self) -> bool:
        """Send MsgID 0x04 RESET_YAW command (0 Bytes payload)."""
        return self._send_raw_frame(MsgID.RESET_YAW.value, b'')

    def _cmd_vel_callback(self, msg: Twist):
        """
        Callback for /cmd_vel subscriber.
        Packs linear.x, linear.y, angular.z into '<fff' (12 Bytes), calculates CRC16,
        and transmits binary frame MsgID 0x02 to ESP32 immediately.
        """
        linear_x = float(msg.linear.x)
        linear_y = float(msg.linear.y)
        angular_z = float(msg.angular.z)
        
        payload = struct.pack('<fff', linear_x, linear_y, angular_z)
        self._send_raw_frame(MsgID.CMD_VEL.value, payload)

    def _timer_serial_read_callback(self):
        """
        100Hz Non-blocking serial stream reader and state machine parser.
        Reads incoming bytes, validates CRC16, and unpacks Telemetry (MsgID 0x01).
        """
        if not self.is_connected or self.serial_port is None:
            return
        
        try:
            bytes_waiting = self.serial_port.in_waiting
            if bytes_waiting <= 0:
                return
            
            raw_bytes = self.serial_port.read(bytes_waiting)
            for byte in raw_bytes:
                result = self.parser.feed_byte(byte)
                if result is not None:
                    msg_id, payload, rx_crc = result
                    
                    # Verify CRC16: calculated over [MsgID + Length + Payload]
                    crc_data = struct.pack('BB', msg_id, len(payload)) + payload
                    calc_crc = calculate_crc16(crc_data)
                    
                    if rx_crc != calc_crc:
                        self.get_logger().warn(
                            f'CRC16 mismatch! MsgID=0x{msg_id:02X}, Calc=0x{calc_crc:04X}, Rx=0x{rx_crc:04X}'
                        )
                        continue
                    
                    # Process Telemetry Frame (MsgID 0x01)
                    if msg_id == MsgID.TELEMETRY.value:
                        telemetry = BinaryProtocol.unpack_telemetry(payload)
                        if telemetry is not None:
                            self.latest_telemetry = telemetry
                            self._publish_sensor_data(telemetry)
                        else:
                            self.get_logger().warn('Failed to unpack telemetry payload')
                    else:
                        self.get_logger().debug(f'Received MsgID=0x{msg_id:02X}, length={len(payload)}')

        except serial.SerialException as e:
            self.get_logger().error(f'Serial exception during read: {e}')
            self.is_connected = False
        except Exception as e:
            self.get_logger().error(f'Unexpected error in serial parser: {e}')

    def _publish_sensor_data(self, telemetry: Dict[str, Any]):
        """Publish IMU and Range sensor messages from telemetry."""
        now = self.get_clock().now().to_msg()
        
        # 1. Publish /imu/data_raw (sensor_msgs/msg/Imu)
        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = 'imu_link'
        
        # Acceleration (m/s^2)
        imu_msg.linear_acceleration.x = float(telemetry['accel_x'])
        imu_msg.linear_acceleration.y = float(telemetry['accel_y'])
        imu_msg.linear_acceleration.z = float(telemetry['accel_z'])
        
        # Angular velocity (rad/s)
        imu_msg.angular_velocity.x = float(telemetry['gyro_x'])
        imu_msg.angular_velocity.y = float(telemetry['gyro_y'])
        imu_msg.angular_velocity.z = float(telemetry['gyro_z'])
        
        # Convert Roll, Pitch, Yaw from degrees to radians -> Quaternions
        roll_rad = math.radians(float(telemetry['roll']))
        pitch_rad = math.radians(float(telemetry['pitch']))
        yaw_rad = math.radians(float(telemetry['yaw']))
        
        qx, qy, qz, qw = euler_to_quaternion(roll_rad, pitch_rad, yaw_rad)
        imu_msg.orientation.x = qx
        imu_msg.orientation.y = qy
        imu_msg.orientation.z = qz
        imu_msg.orientation.w = qw
        
        self.pub_imu.publish(imu_msg)
        
        # 2. Publish /range/front (sensor_msgs/msg/Range) - cm to meters
        front_msg = Range()
        front_msg.header.stamp = now
        front_msg.header.frame_id = 'front_sensor'
        front_msg.radiation_type = Range.ULTRASOUND
        front_msg.field_of_view = 0.26
        front_msg.min_range = 0.02
        front_msg.max_range = 4.0
        front_msg.range = float(telemetry['front_distance']) / 100.0  # cm -> meters
        self.pub_range_front.publish(front_msg)
        
        # 3. Publish /range/rear (sensor_msgs/msg/Range) - cm to meters
        rear_msg = Range()
        rear_msg.header.stamp = now
        rear_msg.header.frame_id = 'rear_sensor'
        rear_msg.radiation_type = Range.ULTRASOUND
        rear_msg.field_of_view = 0.26
        rear_msg.min_range = 0.02
        rear_msg.max_range = 4.0
        rear_msg.range = float(telemetry['rear_distance']) / 100.0  # cm -> meters
        self.pub_range_rear.publish(rear_msg)

    def _timer_status_callback(self):
        """1Hz Publisher for /esp32/status topic."""
        status_msg = String()
        
        if self.latest_telemetry is None:
            status_msg.data = 'Status: Waiting for ESP32 Telemetry...'
            self.pub_status.publish(status_msg)
            return
        
        t = self.latest_telemetry
        modes = {0: 'MANUAL', 1: 'AUTO', 2: 'ROS2'}
        current_mode_str = modes.get(t['current_mode'], f"UNKNOWN({t['current_mode']})")
        
        flags = t['flags']
        mpu_ok = bool(flags & 0x01)
        front_online = bool(flags & 0x02)
        rear_online = bool(flags & 0x04)
        estop = bool(flags & 0x08)
        
        status_str = (
            f"Mode={current_mode_str} | "
            f"PWM:[FL={t['motor_fl_speed']}, FR={t['motor_fr_speed']}, RL={t['motor_rl_speed']}, RR={t['motor_rr_speed']}] | "
            f"Flags:[MPU={'OK' if mpu_ok else 'FAIL'}, Front={'ON' if front_online else 'OFF'}, "
            f"Rear={'ON' if rear_online else 'OFF'}, EStop={'ACTIVE' if estop else 'OFF'}]"
        )
        
        status_msg.data = status_str
        self.pub_status.publish(status_msg)

    def destroy_node(self):
        """
        Auto-Switch Mode on shutdown:
        Sends SET_MODE (target_mode=0 MANUAL, e_stop=1) to ESP32 for safety before closing.
        """
        self.get_logger().info('Shutting down Node... Switching ESP32 to MODE_MANUAL (E-STOP=1)')
        if self.is_connected and self.serial_port is not None:
            try:
                self._send_set_mode(target_mode=0, e_stop=1)
                time.sleep(0.05)
                self.serial_port.close()
            except Exception as e:
                self.get_logger().warn(f'Error during shutdown send: {e}')
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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
