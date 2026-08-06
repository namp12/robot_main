import time
import math
import threading
from typing import List, Tuple


class SpatialMemory:
    """
    Short-Term Spatial Memory System:
    - Dead-end Memory: Blacklists failed headings/directions where obstacle recovery was triggered.
    - Visited Area Memory: Stores recent robot trajectory poses to penalize looping.
    """

    def __init__(self, memory_duration_sec: float = 30.0, visited_grid_res: float = 0.5):
        self.memory_duration_sec = memory_duration_sec
        self.visited_grid_res = visited_grid_res

        # Store tuples of (failed_heading_rad, timestamp)
        self._dead_ends: List[Tuple[float, float]] = []

        # Store dict of (grid_x, grid_y) -> timestamp
        self._visited_grids = {}
        self._lock = threading.Lock()

    def record_dead_end(self, heading_rad: float):
        """Blacklist a heading direction that resulted in a dead end or recovery action."""
        with self._lock:
            self._dead_ends.append((heading_rad, time.time()))

    def record_visited_pose(self, x: float, y: float):
        """Record robot current pose in spatial grid memory."""
        gx = int(round(x / self.visited_grid_res))
        gy = int(round(y / self.visited_grid_res))
        with self._lock:
            self._visited_grids[(gx, gy)] = time.time()

    def is_dead_end_heading(self, heading_rad: float, tolerance_rad: float = 0.5) -> bool:
        """Check if target heading overlaps with a recently blacklisted dead-end heading."""
        now = time.time()
        with self._lock:
            # Clean up old dead-ends
            self._dead_ends = [(h, ts) for h, ts in self._dead_ends if now - ts < self.memory_duration_sec]

            for h, _ in self._dead_ends:
                diff = abs(math.atan2(math.sin(heading_rad - h), math.cos(heading_rad - h)))
                if diff <= tolerance_rad:
                    return True
        return False

    def get_visited_penalty(self, x: float, y: float) -> float:
        """Return a penalty score (0.0 to 1.0) if the target position was recently visited."""
        gx = int(round(x / self.visited_grid_res))
        gy = int(round(y / self.visited_grid_res))
        now = time.time()
        with self._lock:
            if (gx, gy) in self._visited_grids:
                ts = self._visited_grids[(gx, gy)]
                elapsed = now - ts
                if elapsed < self.memory_duration_sec:
                    return 1.0 - (elapsed / self.memory_duration_sec)
        return 0.0
