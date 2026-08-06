import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

from robot_ai.mode_manager.mode_types import RobotMode, ModeContext
from robot_ai.mode_manager.mode_manager import MultiModeManager
from robot_ai.mode_manager.mode_events import ModeEventType


class ModeManagerNode(Node):
    """
    ROS2 Multi-Mode Control System V2 Node.
    Acts as the highest level Mode Coordinator and /cmd_vel Multiplexer (Mux).
    Additive Only & 100% Backward Compatible.
    """

    def __init__(self):
        super().__init__('robot_mode_manager_node')

        self.declare_parameter('default_mode', 'MANUAL')
        default_mode_str = self.get_parameter('default_mode').value

        initial_mode = self._parse_mode_string(default_mode_str)
        self.manager = MultiModeManager(initial_mode=initial_mode)

        # Register event listener callback
        self.manager.event_engine.register_listener(self._on_mode_event)

        # Subscriptions
        self.create_subscription(String, '/robot/command', self._on_robot_command, 10)
        self.create_subscription(String, '/autonomy/set_mode', self._on_set_mode_topic, 10)
        self.create_subscription(Twist, '/cmd_vel_manual', self._on_cmd_vel_manual, 10)
        self.create_subscription(Twist, '/cmd_vel_auto', self._on_cmd_vel_auto, 10)

        # Output Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mode_status_pub = self.create_publisher(String, '/autonomy/mode', 10)

        # 5Hz Status Telemetry Timer (200ms)
        self.create_timer(0.2, self._publish_mode_status)

        self.get_logger().info(
            f'🎛️ Multi-Mode Control System V2 ONLINE (DefaultMode={initial_mode.name})'
        )

    def _parse_mode_string(self, mode_str: str) -> RobotMode:
        """Parse string to RobotMode enum safely."""
        clean_str = mode_str.strip().upper().replace("MODE_", "")
        for mode in RobotMode:
            if mode.name == clean_str:
                return mode
        return RobotMode.MANUAL

    def _on_robot_command(self, msg: String):
        """Parse voice / web commands for mode transitions."""
        cmd_text = msg.data.strip().lower()

        if any(w in cmd_text for w in ["dừng khẩn cấp", "khẩn cấp", "emergency"]):
            self.manager.trigger_emergency_stop()
            self.get_logger().error("EMERGENCY STOP TRIGGERED VIA COMMAND")
        elif "khôi phục" in cmd_text or "reset emergency" in cmd_text:
            self.manager.reset_emergency_stop()
            self.get_logger().info("EMERGENCY STOP RESET TO MANUAL")
        elif "chế độ tự hành" in cmd_text or "mode auto" in cmd_text or "explore" in cmd_text:
            self.manager.switch_mode(RobotMode.AUTO_EXPLORE)
        elif "chế độ lái tay" in cmd_text or "mode manual" in cmd_text:
            self.manager.switch_mode(RobotMode.MANUAL)
        elif "bám theo" in cmd_text or "follow person" in cmd_text:
            self.manager.switch_mode(RobotMode.FOLLOW_PERSON)
        elif "trợ lý giọng nói" in cmd_text or "voice assistant" in cmd_text:
            self.manager.switch_mode(RobotMode.VOICE_ASSISTANT)

    def _on_set_mode_topic(self, msg: String):
        """Direct topic handler for mode switching."""
        target_mode = self._parse_mode_string(msg.data)
        success, reason = self.manager.switch_mode(target_mode)
        if success:
            self.get_logger().info(f"Mode set to {target_mode.name}: {reason}")
        else:
            self.get_logger().warn(f"Failed to set mode {target_mode.name}: {reason}")

    def _on_cmd_vel_manual(self, msg: Twist):
        """Filter and forward manual cmd_vel input if MANUAL or SAFE_MANUAL mode is active."""
        filtered_cmd = self.manager.filter_cmd_vel(RobotMode.MANUAL, msg)
        if filtered_cmd is None:
            filtered_cmd = self.manager.filter_cmd_vel(RobotMode.SAFE_MANUAL, msg)

        if filtered_cmd is not None:
            self.cmd_vel_pub.publish(filtered_cmd)

    def _on_cmd_vel_auto(self, msg: Twist):
        """Filter and forward autonomous cmd_vel input if AUTO_EXPLORE mode is active."""
        filtered_cmd = self.manager.filter_cmd_vel(RobotMode.AUTO_EXPLORE, msg)
        if filtered_cmd is not None:
            self.cmd_vel_pub.publish(filtered_cmd)

    def _publish_mode_status(self):
        """Publish JSON status telemetry snapshot to /autonomy/mode for Web Dashboard."""
        status = self.manager.get_status_telemetry()
        payload = {
            "current_mode": status.current_mode,
            "previous_mode": status.previous_mode,
            "priority_level": status.priority_level,
            "is_active": status.is_active,
            "active_controller": status.active_controller,
            "elapsed_time_sec": status.elapsed_time_sec,
            "context_info": status.context_info
        }
        msg = String()
        msg.data = json.dumps(payload)
        self.mode_status_pub.publish(msg)

    def _on_mode_event(self, event_type: ModeEventType, data: dict):
        """Event listener callback logging mode transitions."""
        self.get_logger().info(f"🔔 MODE EVENT [{event_type.name}]: {data}")


def main(args=None):
    rclpy.init(args=args)
    node = ModeManagerNode()
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
