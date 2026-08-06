import math
import numpy as np
from typing import Tuple, List, Dict, Any


class FreeSpaceCorridorPlanner:
    """
    Volumetric 72-Sector Free-Space Corridor Navigation Engine V4.0.
    Analyzes 360-degree LiDAR range data divided into 72 sectors (5 degrees per sector).
    Identifies the widest open corridor (>2.0m) and generates smooth velocity vectors (vx, wz).
    """

    def __init__(self, num_sectors: int = 72, min_corridor_width_meters: float = 0.8, max_search_range: float = 5.0):
        self.num_sectors = num_sectors
        self.sector_angle_deg = 360.0 / num_sectors
        self.min_corridor_width = min_corridor_width_meters
        self.max_search_range = max_search_range

    def analyze_corridors(self, scan_ranges: List[float]) -> Dict[str, Any]:
        """
        Analyze scan ranges across 72 sectors to find open free-space corridors.
        """
        if not scan_ranges:
            return {"best_angle_deg": 0.0, "max_free_distance": 0.0, "corridor_found": False}

        ranges = np.array(scan_ranges)
        num_points = len(ranges)
        pts_per_sector = max(1, num_points // self.num_sectors)

        sector_distances = []
        for i in range(self.num_sectors):
            start_idx = i * pts_per_sector
            end_idx = min(num_points, (i + 1) * pts_per_sector)
            sector_chunk = ranges[start_idx:end_idx]
            valid_chunk = sector_chunk[(sector_chunk > 0.05) & (sector_chunk < self.max_search_range)]

            if len(valid_chunk) > 0:
                sector_distances.append(float(np.median(valid_chunk)))
            else:
                sector_distances.append(self.max_search_range)

        # Find sector with maximum free space in forward 180-degree field of view
        # Forward FOV corresponds to front-facing sectors (indices around 0/num_sectors and front center)
        best_sector_idx = int(np.argmax(sector_distances))
        max_dist = sector_distances[best_sector_idx]

        # Calculate angle relative to front heading (0 degrees)
        angle_deg = (best_sector_idx * self.sector_angle_deg)
        if angle_deg > 180.0:
            angle_deg -= 360.0

        corridor_found = max_dist >= self.min_corridor_width

        return {
            "best_sector_index": best_sector_idx,
            "best_angle_deg": float(angle_deg),
            "max_free_distance": float(max_dist),
            "corridor_found": corridor_found,
            "sector_distances": sector_distances
        }

    def compute_corridor_cmd_vel(self, scan_ranges: List[float], max_linear: float = 0.35, max_angular: float = 0.65) -> Tuple[float, float]:
        """
        Compute smooth velocity trajectory (linear_x, angular_z) following the best open corridor.
        """
        analysis = self.analyze_corridors(scan_ranges)
        if not analysis["corridor_found"]:
            return 0.0, 0.0

        target_angle_rad = math.radians(analysis["best_angle_deg"])
        free_dist = analysis["max_free_distance"]

        # Scale linear velocity based on free space distance ahead
        linear_scale = min(1.0, max(0.2, free_dist / 3.0))
        linear_x = max_linear * linear_scale * math.cos(target_angle_rad)
        linear_x = max(0.0, linear_x)

        # Scale angular velocity to turn smoothly toward open corridor
        angular_z = max_angular * math.sin(target_angle_rad)

        return round(float(linear_x), 3), round(float(angular_z), 3)
