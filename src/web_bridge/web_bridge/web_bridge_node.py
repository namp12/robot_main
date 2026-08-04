#!/usr/bin/env python3
"""
web_bridge_node.py - WebSocket bridge between ROS2 and web dashboard.

Publishes ROS2 telemetry to WebSocket clients and forwards web commands
to ROS2 topics so the web dashboard can control the robot.
"""

import asyncio
import json
import math
import threading
from typing import Dict, Optional

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import String, Float32
from sensor_msgs.msg import Imu, LaserScan
from geometry_msgs.msg import Twist

import websockets


def quaternion_to_euler(x: float, y: float, z: float, w: float):
    # roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


class WebBridgeNode(Node):
    """ROS2 node that bridges telemetry and commands via WebSocket."""

    def __init__(self) -> None:
        super().__init__('web_bridge_node')
        self.declare_parameter('ws_port', 8090)
        self._ws_port = self.get_parameter('ws_port').value
        self._ws_connected_clients: set = set()
        self._latest_telemetry: Dict = {}
        self._callback_group = ReentrantCallbackGroup()
        self._ws_loop: Optional[asyncio.AbstractEventLoop] = None

        # Publishers for outgoing ROS2 commands
        self._cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10, callback_group=self._callback_group
        )
        self._serial_tx_pub = self.create_publisher(
            String, '/esp32/serial_tx', 10, callback_group=self._callback_group
        )

        # Subscribers for incoming telemetry
        self._scan_sub = self.create_subscription(
            LaserScan, '/scan', self._on_scan, 10, callback_group=self._callback_group
        )
        self._mode_sub = self.create_subscription(
            String, '/esp32/mode', self._on_mode, 10, callback_group=self._callback_group
        )
        self._status_sub = self.create_subscription(
            String, '/esp32/status', self._on_status, 10, callback_group=self._callback_group
        )
        self._front_sub = self.create_subscription(
            Float32, '/sensor/front_distance', self._on_front_distance, 10, callback_group=self._callback_group
        )
        self._rear_sub = self.create_subscription(
            Float32, '/sensor/rear_distance', self._on_rear_distance, 10, callback_group=self._callback_group
        )
        self._battery_sub = self.create_subscription(
            Float32, '/sensor/battery', self._on_battery, 10, callback_group=self._callback_group
        )
        self._imu_sub = self.create_subscription(
            Imu, '/imu/data', self._on_imu, 10, callback_group=self._callback_group
        )
        self._encoder_sub = self.create_subscription(
            Float32, '/esp32/encoder_distance', self._on_encoder_distance, 10, callback_group=self._callback_group
        )

        self.get_logger().info(f'Web bridge initialized on port {self._ws_port}')

        # Start WebSocket server in a background thread so it can run
        # alongside the ROS2 MultiThreadedExecutor.
        ws_thread = threading.Thread(target=self._start_ws_thread, daemon=True)
        ws_thread.start()

    def _on_scan(self, msg: LaserScan) -> None:
        self._latest_telemetry['scan'] = {
            'ranges': [float(r) if not math.isinf(r) and not math.isnan(r) else 0.0 for r in msg.ranges],
            'angle_min': float(msg.angle_min),
            'angle_max': float(msg.angle_max),
            'angle_increment': float(msg.angle_increment)
        }
        self._broadcast_telemetry()

    def _on_mode(self, msg: String) -> None:
        self._latest_telemetry['mode'] = msg.data
        self._broadcast_telemetry()

    def _on_status(self, msg: String) -> None:
        self._latest_telemetry['status'] = msg.data
        self._broadcast_telemetry()

    def _on_front_distance(self, msg: Float32) -> None:
        self._latest_telemetry['front_distance'] = msg.data
        self._broadcast_telemetry()

    def _on_imu(self, msg: Imu) -> None:
        # Convert quaternion to euler angles in degrees
        roll, pitch, yaw = quaternion_to_euler(
            msg.orientation.x,
            msg.orientation.y,
            msg.orientation.z,
            msg.orientation.w
        )
        roll_deg = math.degrees(roll)
        pitch_deg = math.degrees(pitch)
        yaw_deg = math.degrees(yaw)

        self._latest_telemetry['roll'] = roll_deg
        self._latest_telemetry['pitch'] = pitch_deg
        self._latest_telemetry['yaw'] = yaw_deg

        # Populate imu_raw for web SensorPanel Accel and Gyro display
        self._latest_telemetry['imu_raw'] = {
            'accel': {
                'x': msg.linear_acceleration.x,
                'y': msg.linear_acceleration.y,
                'z': msg.linear_acceleration.z
            },
            'gyro': {
                'x': msg.angular_velocity.x,
                'y': msg.angular_velocity.y,
                'z': msg.angular_velocity.z
            }
        }

        # Populate pose.yaw for orientation arrow display in map view
        self._latest_telemetry['pose'] = {
            'x': self._latest_telemetry.get('pose', {}).get('x', 2.45),
            'y': self._latest_telemetry.get('pose', {}).get('y', -1.12),
            'yaw': yaw_deg
        }

        self._broadcast_telemetry()

    def _on_rear_distance(self, msg: Float32) -> None:
        self._latest_telemetry['rear_distance'] = msg.data
        self._broadcast_telemetry()

    def _on_battery(self, msg: Float32) -> None:
        self._latest_telemetry['battery'] = msg.data
        self._broadcast_telemetry()

    def _on_encoder_distance(self, msg: Float32) -> None:
        self._latest_telemetry['encoder_distance'] = msg.data
        self._broadcast_telemetry()

    def _broadcast_telemetry(self) -> None:
        if not self._ws_connected_clients or self._ws_loop is None or self._ws_loop.is_closed():
            return
        message = json.dumps({'type': 'telemetry', 'data': self._latest_telemetry})
        for ws in list(self._ws_connected_clients):
            try:
                asyncio.run_coroutine_threadsafe(ws.send(message), self._ws_loop)
            except Exception:
                pass

    def _handle_ws_command(self, message: str) -> None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type')
        if msg_type == 'cmd_vel':
            twist = Twist()
            twist.linear.x = float(data.get('linear_x', 0.0))
            twist.linear.y = float(data.get('linear_y', 0.0))
            twist.angular.z = float(data.get('angular_z', 0.0))
            self._cmd_vel_pub.publish(twist)
        elif msg_type == 'mode':
            mode_map = {'manual': 'mode_manual', 'auto': 'mode_auto', 'ros2': 'mode_ros2'}
            payload = mode_map.get(data.get('mode'))
            if payload:
                out = String()
                out.data = payload
                self._serial_tx_pub.publish(out)
        elif msg_type == 'move':
            direction = str(data.get('direction', '')).lower()
            speed = float(data.get('speed', 150.0))
            scale = max(0.1, min(speed / 150.0, 1.7))

            twist = Twist()
            if direction in ['tien', 'forward']:
                twist.linear.x = 0.25 * scale
            elif direction in ['lui', 'backward']:
                twist.linear.x = -0.25 * scale
            elif direction in ['trai', 'left', 'strafe_left']:
                twist.linear.y = 0.25 * scale
            elif direction in ['phai', 'right', 'strafe_right']:
                twist.linear.y = -0.25 * scale
            elif direction in ['xoay_trai', 'rotate_left']:
                twist.angular.z = 0.60 * scale
            elif direction in ['xoay_phai', 'rotate_right']:
                twist.angular.z = -0.60 * scale
            elif direction in ['cheo_trai', 'cheo_tt', 'diag_fl', 'diag_left']:
                twist.linear.x = 0.20 * scale
                twist.linear.y = 0.20 * scale
            elif direction in ['cheo_phai', 'cheo_tp', 'diag_fr', 'diag_right']:
                twist.linear.x = 0.20 * scale
                twist.linear.y = -0.20 * scale
            elif direction in ['xoay_tron', 'spin']:
                twist.angular.z = 0.80 * scale
            else:
                twist.linear.x = 0.0
                twist.linear.y = 0.0
                twist.angular.z = 0.0

            self._cmd_vel_pub.publish(twist)
        elif msg_type == 'beep':
            out = String()
            out.data = 'beep 500'
            self._serial_tx_pub.publish(out)
        elif msg_type == 'text':
            out = String()
            out.data = data.get('data', '')
            self._serial_tx_pub.publish(out)

    async def _ws_handler(self, websocket, path: Optional[str] = None) -> None:
        self._ws_connected_clients.add(websocket)
        self.get_logger().info(f'Web client connected: {websocket.remote_address}')
        try:
            async for message in websocket:
                self._handle_ws_command(message)
        except websockets.ConnectionClosed as exc:
            self.get_logger().info(f'WebSocket connection closed: {exc}')
        except asyncio.CancelledError:
            self.get_logger().info('WebSocket handler cancelled')
        except Exception as exc:
            self.get_logger().warning(f'WebSocket error: {exc}')
        finally:
            self._ws_connected_clients.discard(websocket)
            self.get_logger().info('Web client disconnected')

    def _start_ws_thread(self) -> None:
        asyncio.run(self._run_ws())

    async def _run_ws(self) -> None:
        self._ws_loop = asyncio.get_running_loop()
        try:
            async with websockets.serve(self._ws_handler, '0.0.0.0', self._ws_port, reuse_port=True):
                self.get_logger().info(f'WebSocket server started on port {self._ws_port}')
                await asyncio.Future()
        except TypeError:
            async with websockets.serve(self._ws_handler, '0.0.0.0', self._ws_port):
                self.get_logger().info(f'WebSocket server started on port {self._ws_port}')
                await asyncio.Future()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WebBridgeNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
