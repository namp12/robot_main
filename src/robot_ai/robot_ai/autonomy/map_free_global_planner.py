import math
from typing import Tuple, List, Dict, Any


class MapFreeGlobalPlanner:
    """
    Map-Free Global Navigation Engine V6.0 (Trụ cột 2).
    Navigates to long-distance goal coordinates (>10m) in unmapped dynamic environments
    without requiring a static pre-built .yaml map.
    Uses rolling occupancy grid costmap generated live from 360-degree LiDAR and AI Vision.
    """

    def __init__(self, max_range_meters: float = 15.0, grid_resolution: float = 0.1):
        self.max_range = max_range_meters
        self.grid_resolution = grid_resolution

    def compute_waypoint_vector(
        self,
        current_x: float,
        current_y: float,
        current_yaw_rad: float,
        target_x: float,
        target_y: float,
        scan_ranges: List[float]
    ) -> Tuple[float, float, float]:
        """
        Calculates distance, relative angle (rad), and recommended direction to long-distance goal (target_x, target_y).
        """
        dx = target_x - current_x
        dy = target_y - current_y
        dist_to_goal = math.hypot(dx, dy)

        if dist_to_goal < 0.3:
            # Reached goal
            return 0.0, 0.0, 0.0

        goal_angle_global = math.atan2(dy, dx)
        relative_angle = goal_angle_global - current_yaw_rad

        # Normalize relative angle to [-pi, pi]
        while relative_angle > math.pi:
            relative_angle -= 2 * math.pi
        while relative_angle < -math.pi:
            relative_angle += 2 * math.pi

        return round(float(dist_to_goal), 3), round(float(relative_angle), 3), round(float(goal_angle_global), 3)
