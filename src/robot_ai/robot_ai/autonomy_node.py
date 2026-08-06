import json
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from sensor_msgs.msg import LaserScan, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, PoseStamped

from robot_ai.autonomy.local_costmap import LocalCostmap
from robot_ai.autonomy.perception_fusion import PerceptionFusionManager
from robot_ai.autonomy.spatial_memory import SpatialMemory
from robot_ai.autonomy.local_planner import LocalPlanner
from robot_ai.autonomy.behavior_fsm import BehaviorManager, RobotState
from robot_ai.autonomy.velocity_planner import DynamicVelocityPlanner
from robot_ai.autonomy.health_watchdog import HealthWatchdog


class AutonomyNode(Node):
    """
    Autonomous Navigation Stack V3 Node for Kim Qui Robot.
    Lightweight, Non-Nav2 Local Autonomy & Intelligent Obstacle Avoidance Engine.
    """

    def __init__(self):
        super().__init__('robot_autonomy_node')

        # Declare ROS2 Parameters
        self.declare_parameter('simulation', False)
        self.declare_parameter('autonomy_enabled', True)
        self.declare_parameter('max_linear_speed', 0.35)
        self.declare_parameter('watchdog_enabled', False)
        self.declare_parameter('max_angular_speed', 0.60)
        self.declare_parameter('inflation_radius', 0.35)
        self.declare_parameter('sector_count', 36)

        self.simulation = self.get_parameter('simulation').value
        self.autonomy_enabled = self.get_parameter('autonomy_enabled').value
        self.watchdog_enabled = self.get_parameter('watchdog_enabled').value
        max_lin = self.get_parameter('max_linear_speed').value
        max_ang = self.get_parameter('max_angular_speed').value
        inf_rad = self.get_parameter('inflation_radius').value
        sec_cnt = self.get_parameter('sector_count').value

        # Initialize Submodules
        self.costmap = LocalCostmap(size_meters=6.0, resolution=0.05, inflation_radius=inf_rad)
        self.fusion = PerceptionFusionManager()
        self.spatial_mem = SpatialMemory(memory_duration_sec=30.0)
        self.planner = LocalPlanner(num_sectors=sec_cnt)
        self.behavior = BehaviorManager()
        self.velocity_planner = DynamicVelocityPlanner(max_linear_speed=max_lin, max_angular_speed=max_ang)
        self.watchdog = HealthWatchdog(timeout_sec=3.0, startup_grace_sec=15.0)

        # Default initial state to EXPLORE when enabled
        if self.autonomy_enabled:
            self.behavior.set_state(RobotState.EXPLORE)

        # Standard Compatible QoS Subscriptions for /scan (compatible with all LiDAR drivers)
        from rclpy.qos import qos_profile_sensor_data
        self.create_subscription(LaserScan, '/scan', self._on_scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self.create_subscription(Imu, '/imu/data', self._on_imu, 10)
        self.create_subscription(String, '/detection', self._on_detection, 10)
        self.create_subscription(String, '/robot/command', self._on_command, 10)

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/autonomy/status', 10)
        self.debug_heading_pub = self.create_publisher(PoseStamped, '/autonomy/chosen_heading', 10)

        # 10Hz Control Loop Timer (100ms)
        self.create_timer(0.1, self._control_loop)

        self.get_logger().info(
            f'🤖 Autonomous Navigation Stack V3 ONLINE (Simulation={self.simulation}, Enabled={self.autonomy_enabled}, State={self.behavior.get_state().name})'
        )

    def _on_scan(self, msg: LaserScan):
        """LiDAR LaserScan Callback."""
        self.watchdog.touch_lidar()

        # Update Local Rolling Costmap
        self.costmap.update_from_scan(
            list(msg.ranges),
            msg.angle_min,
            msg.angle_increment,
            msg.range_min,
            msg.range_max
        )

        # Compute Sector Min Distances
        sector_dists = self.planner.compute_sector_distances(
            list(msg.ranges),
            msg.angle_min,
            msg.angle_increment
        )

        # Extract directional minimal distances for perception fusion summary
        front = min(sector_dists[0], sector_dists[1], sector_dists[-1])
        left = min(sector_dists[8:12]) if len(sector_dists) >= 12 else 999.0
        right = min(sector_dists[24:28]) if len(sector_dists) >= 28 else 999.0
        rear = min(sector_dists[16:20]) if len(sector_dists) >= 20 else 999.0

        self.fusion.update_lidar_summary(front, left, right, rear)
        self.latest_sector_dists = sector_dists

    def _on_odom(self, msg: Odometry):
        """Odometry Callback."""
        self.watchdog.touch_odom()
        px = msg.pose.pose.position.x
        py = msg.pose.pose.position.y

        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        self.fusion.update_pose(px, py, yaw)
        self.spatial_mem.record_visited_pose(px, py)

    def _on_imu(self, msg: Imu):
        """IMU Callback."""
        self.watchdog.touch_imu()

    def _on_detection(self, msg: String):
        """Camera AI YOLO Object Detection Callback."""
        self.watchdog.touch_camera()
        self.fusion.update_vision_detections(msg.data)

    def _on_command(self, msg: String):
        """Voice or Web Command Callback."""
        cmd_text = msg.data.strip().lower()
        if "tự hành" in cmd_text or "autonomy" in cmd_text or "explore" in cmd_text:
            self.autonomy_enabled = True
            self.behavior.set_state(RobotState.EXPLORE)
            self.get_logger().info("AUTONOMY MODE: ACTIVATED")
        elif "dừng" in cmd_text or "stop" in cmd_text or "thỦ công" in cmd_text:
            self.autonomy_enabled = False
            self.behavior.set_state(RobotState.IDLE)
            self.get_logger().info("AUTONOMY MODE: DEACTIVATED")

    def _control_loop(self):
        """Main 10Hz Control Loop executing Layered Architecture Pipeline."""
        # 1. Safety Watchdog Health Check
        is_healthy, health_reason = self.watchdog.check_health()
        if not is_healthy:
            if self.watchdog_enabled:
                self.get_logger().error(f"HEALTH MONITOR FAILURE: {health_reason}")
                self.behavior.trigger_emergency_stop()
            else:
                self.get_logger().warning(f"HEALTH MONITOR WARNING: {health_reason}")

        current_state = self.behavior.get_state()
        world_model = self.fusion.get_world_model()

        if not self.autonomy_enabled or current_state == RobotState.IDLE:
            self._publish_status("IDLE", 0.0, 0.0, world_model.confidence_score)
            return

        if current_state == RobotState.EMERGENCY_STOP:
            self._send_cmd_vel(self.velocity_planner.stop())
            self._publish_status("EMERGENCY_STOP", 0.0, 0.0, 0.0)
            return

        # 2. Obstacle Proximity Check
        if world_model.min_front_dist < 0.30:
            # Front obstacle too close! Trigger Recovery or Obstacle Avoidance
            if self.behavior.get_state_duration() > 2.0:
                self.behavior.set_state(RobotState.RECOVERY)
            else:
                self.behavior.set_state(RobotState.AVOID_OBSTACLE)

        # 3. State Machine Decision & Planning Execution
        if current_state == RobotState.RECOVERY:
            # Multi-step Intelligent Recovery: Back up & Turn away
            rec_count = self.behavior.increment_recovery_count()
            self.get_logger().warn(f"EXECUTING RECOVERY ATTEMPT #{rec_count}")

            # Blacklist front heading in spatial memory
            self.spatial_mem.record_dead_end(0.0)

            # Generate backing-up Twist command
            cmd = Twist()
            cmd.linear.x = -0.15
            cmd.angular.z = 0.40 if (rec_count % 2 == 1) else -0.40
            self._send_cmd_vel(cmd)

            if self.behavior.get_state_duration() > 1.5:
                self.behavior.set_state(RobotState.EXPLORE)
            self._publish_status("RECOVERY", cmd.linear.x, cmd.angular.z, world_model.confidence_score)
            return

        # Default Autonomy Behavior: Local Planning & Free Space Selection
        sector_dists = getattr(self, 'latest_sector_dists', [999.0] * 36)
        desired_heading, speed_scale, best_sector = self.planner.plan(
            sector_dists,
            world_model,
            self.spatial_mem,
            target_heading_rad=0.0
        )

        # Compute smooth Twist motion profile
        cmd = self.velocity_planner.compute_cmd_vel(
            desired_heading,
            speed_scale,
            world_model.min_front_dist,
            dt=0.1
        )

        # Publish command to /cmd_vel
        self._send_cmd_vel(cmd)

        # Publish status telemetry & debug visualization
        self._publish_status(
            current_state.name,
            cmd.linear.x,
            cmd.angular.z,
            world_model.confidence_score
        )
        self._publish_debug_heading(desired_heading)

    def _send_cmd_vel(self, cmd: Twist):
        """Send Twist command to /cmd_vel unless in simulation mode."""
        if not self.simulation:
            self.cmd_vel_pub.publish(cmd)

    def _publish_status(self, state_name: str, linear_x: float, angular_z: float, confidence: float):
        """Publish JSON status telemetry to /autonomy/status."""
        payload = {
            "timestamp": time.time(),
            "state": state_name,
            "simulation": self.simulation,
            "linear_x": round(linear_x, 3),
            "angular_z": round(angular_z, 3),
            "confidence": round(confidence, 2)
        }
        msg = String()
        msg.data = json.dumps(payload)
        self.status_pub.publish(msg)

    def _publish_debug_heading(self, heading_rad: float):
        """Publish PoseStamped debug marker for chosen heading direction."""
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_footprint"
        msg.pose.orientation.z = math.sin(heading_rad / 2.0)
        msg.pose.orientation.w = math.cos(heading_rad / 2.0)
        self.debug_heading_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = AutonomyNode()
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
