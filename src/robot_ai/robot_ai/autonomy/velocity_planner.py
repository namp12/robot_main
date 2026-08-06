import time
import math
from geometry_msgs.msg import Twist


class DynamicVelocityPlanner:
    """
    Dynamic Velocity Planner & Smooth Motion Profiler.
    Applies acceleration/deceleration ramps, curvature speed limiting, and heading PID.
    Prevents jerky motor movements or sudden stop jolts.
    """

    def __init__(
        self,
        max_linear_speed: float = 0.20,
        max_angular_speed: float = 0.35,
        max_acceleration: float = 0.25,
        kp_angular: float = 1.0
    ):
        self.max_linear_speed = max_linear_speed
        self.max_angular_speed = max_angular_speed
        self.max_acceleration = max_acceleration
        self.kp_angular = kp_angular

        self._curr_linear = 0.0
        self._curr_angular = 0.0
        self._last_update_ts = time.time()

    def compute_cmd_vel(
        self,
        target_heading_rad: float,
        speed_scale: float,
        obstacle_dist: float,
        dt: float = 0.1
    ) -> Twist:
        """Compute smooth Twist command based on target heading, speed scale, and obstacle proximity."""
        # 1. Heading error
        heading_err = math.atan2(math.sin(target_heading_rad), math.cos(target_heading_rad))

        # 2. Target angular velocity (P controller)
        target_angular = self.kp_angular * heading_err
        target_angular = max(-self.max_angular_speed, min(self.max_angular_speed, target_angular))

        # 3. Target linear velocity (Curvature & Obstacle Proximity scaling)
        curvature_factor = max(0.2, 1.0 - (abs(heading_err) / (math.pi / 2.0)))
        obstacle_factor = 1.0
        if obstacle_dist < 0.8:
            obstacle_factor = max(0.0, (obstacle_dist - 0.3) / 0.5)

        target_linear = self.max_linear_speed * speed_scale * curvature_factor * obstacle_factor

        # 4. Apply Ramp Acceleration / Deceleration limit
        max_vel_change = self.max_acceleration * dt
        lin_diff = target_linear - self._curr_linear
        lin_diff = max(-max_vel_change * 1.5, min(max_vel_change, lin_diff))
        self._curr_linear += lin_diff

        ang_diff = target_angular - self._curr_angular
        ang_diff = max(-max_vel_change * 2.0, min(max_vel_change * 2.0, ang_diff))
        self._curr_angular += ang_diff

        # Build ROS2 Twist Message
        cmd = Twist()
        cmd.linear.x = float(self._curr_linear)
        cmd.angular.z = float(self._curr_angular)
        return cmd

    def stop(self) -> Twist:
        """Return zero Twist command immediately."""
        self._curr_linear = 0.0
        self._curr_angular = 0.0
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        return cmd
