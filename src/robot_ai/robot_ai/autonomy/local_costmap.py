import numpy as np
import math
import threading
from typing import Tuple, List, Optional


class LocalCostmap:
    """
    Local Rolling Costmap (5m ~ 8m) updated continuously from 360 LiDAR scan data.
    Does NOT use Nav2 or global SLAM map.
    Grid-based representation with obstacle safety inflation buffer.
    """

    def __init__(
        self,
        size_meters: float = 6.0,
        resolution: float = 0.05,
        inflation_radius: float = 0.35,
        max_cost: int = 100
    ):
        self.size_meters = size_meters
        self.resolution = resolution
        self.grid_dim = int(size_meters / resolution)  # e.g., 6.0 / 0.05 = 120 cells
        self.center_idx = self.grid_dim // 2            # Robot is at (60, 60)
        self.inflation_radius = inflation_radius
        self.inflation_cells = int(math.ceil(inflation_radius / resolution))
        self.max_cost = max_cost

        # 0 = Free, 100 = Lethal Obstacle, 1..99 = Inflated Cost
        self._costmap = np.zeros((self.grid_dim, self.grid_dim), dtype=np.uint8)
        self._lock = threading.Lock()

    def update_from_scan(self, ranges: List[float], angle_min: float, angle_increment: float, range_min: float, range_max: float):
        """Update rolling costmap cells from raw LiDAR ranges."""
        new_costmap = np.zeros((self.grid_dim, self.grid_dim), dtype=np.uint8)
        obstacle_coords = []

        for i, r in enumerate(ranges):
            if math.isnan(r) or math.isinf(r) or r < range_min or r > range_max:
                continue

            angle = angle_min + i * angle_increment
            # X forward, Y left in robot base frame
            x = r * math.cos(angle)
            y = r * math.sin(angle)

            grid_x = int(self.center_idx + round(x / self.resolution))
            grid_y = int(self.center_idx + round(y / self.resolution))

            if 0 <= grid_x < self.grid_dim and 0 <= grid_y < self.grid_dim:
                new_costmap[grid_x, grid_y] = self.max_cost
                obstacle_coords.append((grid_x, grid_y))

        # Apply Obstacle Inflation Buffer
        if obstacle_coords:
            for gx, gy in obstacle_coords:
                min_x = max(0, gx - self.inflation_cells)
                max_x = min(self.grid_dim, gx + self.inflation_cells + 1)
                min_y = max(0, gy - self.inflation_cells)
                max_y = min(self.grid_dim, gy + self.inflation_cells + 1)

                for ix in range(min_x, max_x):
                    for iy in range(min_y, max_y):
                        dist_cells = math.hypot(ix - gx, iy - gy)
                        if dist_cells <= self.inflation_cells:
                            cost = int(self.max_cost * (1.0 - (dist_cells / (self.inflation_cells + 1))))
                            if cost > new_costmap[ix, iy]:
                                new_costmap[ix, iy] = cost

        with self._lock:
            self._costmap = new_costmap

    def get_cost(self, rel_x: float, rel_y: float) -> int:
        """Get cost at relative robot coordinates (x forward, y left)."""
        gx = int(self.center_idx + round(rel_x / self.resolution))
        gy = int(self.center_idx + round(rel_y / self.resolution))
        with self._lock:
            if 0 <= gx < self.grid_dim and 0 <= gy < self.grid_dim:
                return int(self._costmap[gx, gy])
            return self.max_cost

    def get_costmap_data(self) -> Tuple[np.ndarray, float, float]:
        """Return thread-safe snapshot of costmap array, resolution, and size."""
        with self._lock:
            return self._costmap.copy(), self.resolution, self.size_meters
