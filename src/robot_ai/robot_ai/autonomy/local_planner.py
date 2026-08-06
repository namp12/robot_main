import math
from typing import List, Tuple, Optional
from robot_ai.autonomy.local_costmap import LocalCostmap
from robot_ai.autonomy.perception_fusion import WorldModel
from robot_ai.autonomy.spatial_memory import SpatialMemory


class LocalPlanner:
    """
    Non-Nav2 Sector-Based Local Path Planner.
    Divides 360 degrees into 36 sectors (10 degrees each).
    Evaluates candidate directions via multi-criteria scoring:
    Score = w1 * Distance + w2 * Width + w3 * Safety - w4 * HeadingDelta - w5 * VisitedPenalty
    """

    def __init__(self, num_sectors: int = 36):
        self.num_sectors = num_sectors
        self.sector_angle = (2.0 * math.pi) / num_sectors  # 10 degrees in radians

    def compute_sector_distances(self, ranges: List[float], angle_min: float, angle_inc: float) -> List[float]:
        """Group 360 raw LiDAR points into 36 angular sector minimum distances."""
        sector_dists = [999.0] * self.num_sectors

        for i, r in enumerate(ranges):
            if math.isnan(r) or math.isinf(r) or r <= 0.05:
                continue
            angle = angle_min + i * angle_inc
            # Normalize angle to [0, 2*pi)
            norm_angle = (angle + 2.0 * math.pi) % (2.0 * math.pi)
            sec_idx = int(norm_angle / self.sector_angle) % self.num_sectors

            if r < sector_dists[sec_idx]:
                sector_dists[sec_idx] = r

        return sector_dists

    def plan(
        self,
        sector_dists: List[float],
        world_model: WorldModel,
        spatial_memory: SpatialMemory,
        target_heading_rad: Optional[float] = 0.0
    ) -> Tuple[float, float, int]:
        """
        Evaluate candidate sectors and select optimal heading angle (radians), desired speed scale, and best sector index.
        Returns: (desired_heading_angle_rad, speed_scale, best_sector_index)
        """
        best_score = -999999.0
        best_sector = 0
        best_angle = 0.0

        for i in range(self.num_sectors):
            angle = i * self.sector_angle
            # Normalize angle to [-pi, pi] for robot base frame
            norm_heading = math.atan2(math.sin(angle), math.cos(angle))

            dist = sector_dists[i]
            if dist < 0.30:
                continue  # Skip sectors that are dangerously close / lethal

            # Sector width calculation (averaging adjacent sectors)
            prev_dist = sector_dists[(i - 1) % self.num_sectors]
            next_dist = sector_dists[(i + 1) % self.num_sectors]
            width_score = min(dist, prev_dist, next_dist)

            # Check if this heading is in dead-end blacklist
            if spatial_memory.is_dead_end_heading(norm_heading):
                continue

            # Heading alignment score (prefer forward 0 rad or target heading)
            target = target_heading_rad if target_heading_rad is not None else 0.0
            heading_diff = abs(math.atan2(math.sin(norm_heading - target), math.cos(norm_heading - target)))

            # Visited penalty
            eval_x = world_model.robot_x + min(dist, 1.5) * math.cos(world_model.robot_yaw + norm_heading)
            eval_y = world_model.robot_y + min(dist, 1.5) * math.sin(world_model.robot_yaw + norm_heading)
            visited_pen = spatial_memory.get_visited_penalty(eval_x, eval_y)

            # Multi-Criteria Scoring Formula
            score = (
                (2.0 * min(dist, 4.0)) +
                (1.5 * min(width_score, 3.0)) -
                (1.8 * heading_diff) -
                (3.0 * visited_pen)
            )

            if score > best_score:
                best_score = score
                best_sector = i
                best_angle = norm_heading

        # Compute recommended speed scale (0.0 to 1.0) based on free distance in best sector
        best_dist = sector_dists[best_sector]
        if best_dist > 2.0:
            speed_scale = 1.0
        elif best_dist > 0.8:
            speed_scale = 0.6
        elif best_dist > 0.4:
            speed_scale = 0.3
        else:
            speed_scale = 0.0

        return best_angle, speed_scale, best_sector
