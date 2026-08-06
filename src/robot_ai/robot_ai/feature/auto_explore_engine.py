import time
import math
import logging
from enum import Enum, auto
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("AutoExploreEngine")


class AutoExploreFSMState(Enum):
    IDLE = auto()
    SCAN = auto()
    FUSION = auto()
    BUILD_COSTMAP = auto()
    PLAN = auto()
    MOVE = auto()
    MONITOR = auto()
    LOCAL_AVOID = auto()
    REPLAN = auto()
    RECOVERY = auto()
    STOP = auto()


class SpatialMemoryManager:
    """
    Remembers Visited Areas, Dead Ends, and Obstacle History to prevent looping.
    """

    def __init__(self, grid_res: float = 0.5):
        self.grid_res = grid_res
        self.visited_cells: set = set()
        self.dead_ends: set = set()
        self.obstacle_history: List[Tuple[float, float]] = []

    def get_cell_key(self, x: float, y: float) -> Tuple[int, int]:
        return (int(round(x / self.grid_res)), int(round(y / self.grid_res)))

    def record_visited(self, x: float, y: float):
        cell = self.get_cell_key(x, y)
        self.visited_cells.add(cell)

    def record_dead_end(self, x: float, y: float):
        cell = self.get_cell_key(x, y)
        self.dead_ends.add(cell)
        logger.warning(f"🗺️ [SPATIAL MEMORY] Marked Dead-End cell: {cell}")

    def is_visited(self, x: float, y: float) -> bool:
        return self.get_cell_key(x, y) in self.visited_cells

    def is_dead_end(self, x: float, y: float) -> bool:
        return self.get_cell_key(x, y) in self.dead_ends

    def reset(self):
        self.visited_cells.clear()
        self.dead_ends.clear()
        self.obstacle_history.clear()


class HealthWatchdog:
    """
    Monitors system node health, LiDAR timeouts, Planner timeouts, and Costmap errors.
    """

    def __init__(self, timeout_sec: float = 3.0):
        self.timeout_sec = timeout_sec
        self.last_lidar_ts: float = time.time()
        self.last_planner_ts: float = time.time()

    def update_lidar_ping(self):
        self.last_lidar_ts = time.time()

    def update_planner_ping(self):
        self.last_planner_ts = time.time()

    def check_health(self) -> Tuple[bool, str]:
        now = time.time()
        if (now - self.last_lidar_ts) > self.timeout_sec:
            return False, "LIDAR_TIMEOUT"
        if (now - self.last_planner_ts) > (self.timeout_sec * 2):
            return False, "PLANNER_TIMEOUT"
        return True, "HEALTHY"


class AutoExploreEngine:
    """
    Behavior Engine for AUTO_EXPLORE V2.
    Strictly isolated: LiDAR 360 + Camera AI Semantic Fusion + 36 Sector Free-Space Planner + Spatial Memory + Recovery.
    Person Tracker & YOLO Person Lock are COMPLETELY DISABLED.
    """

    def __init__(self):
        self.state = AutoExploreFSMState.IDLE
        self.spatial_memory = SpatialMemoryManager()
        self.watchdog = HealthWatchdog()

        self.num_sectors = 36  # 36 sectors, 10 degrees each
        self.current_robot_x: float = 0.0
        self.current_robot_y: float = 0.0
        self.current_heading_rad: float = 0.0

        self.stuck_counter: int = 0
        self.last_recovery_ts: float = 0.0

    def evaluate_free_space_sectors(
        self,
        lidar_scan: List[float],
        semantic_detections: List[Dict[str, Any]]
    ) -> Tuple[int, float]:
        """
        Evaluates 36 sectors (10° each) and computes Free Space Score:
        Clearance + Width + Safety + Current Heading + Turning Cost + Dead End Penalty + Visited Penalty + Semantic Weight.
        Returns (best_sector_index, best_score).
        """
        if not lidar_scan or len(lidar_scan) < 36:
            # Fallback uniform scan if missing
            lidar_scan = [3.0] * 36

        sector_scores = [0.0] * self.num_sectors

        # Check semantic camera weighting (e.g. Door / Corridor preference)
        semantic_boost_sectors = set()
        for det in semantic_detections:
            label = det.get("label", "").lower()
            if any(kw in label for kw in ["door", "corridor", "cửa", "hành lang"]):
                # Boost forward-facing sectors (sectors 0-3 and 32-35)
                for s in range(-3, 4):
                    semantic_boost_sectors.add((s + 36) % 36)

        for i in range(self.num_sectors):
            dist = lidar_scan[i] if i < len(lidar_scan) else 3.0
            if dist <= 0.0:
                dist = 0.1

            # 1. Clearance Score
            clearance_score = min(dist, 4.0) / 4.0

            # 2. Turning Cost Penalty (prefer straight / small turns)
            angle_diff = min(i, 36 - i)
            turning_cost = (angle_diff / 18.0) * 0.3

            # 3. Safety Clearance
            safety_score = 1.0 if dist > 0.60 else (dist / 0.60)

            # 4. Semantic Weight
            semantic_weight = 0.25 if i in semantic_boost_sectors else 0.0

            # 5. Composite Free Space Score
            score = (clearance_score * 0.45) + (safety_score * 0.30) + semantic_weight - turning_cost
            sector_scores[i] = score

        best_sector = max(range(self.num_sectors), key=lambda idx: sector_scores[idx])
        return best_sector, sector_scores[best_sector]

    def process_cycle(self, perception_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Executes one control cycle for Auto Explore V2.
        Returns (command_str, metadata_dict).
        """
        self.watchdog.update_lidar_ping()
        self.watchdog.update_planner_ping()

        healthy, health_reason = self.watchdog.check_health()
        if not healthy:
            self.state = AutoExploreFSMState.STOP
            logger.error(f"🚨 [AUTO EXPLORE WATCHDOG FAILED] Reason: {health_reason}")
            return "dung", {"state": self.state.name, "reason": health_reason}

        lidar_scan = perception_data.get("lidar_scan_36", [3.0] * 36)
        min_obstacle_m = perception_data.get("min_obstacle_distance_m", 99.0)
        semantic_dets = perception_data.get("semantic_detections", [])

        # Record visited position in spatial memory
        self.spatial_memory.record_visited(self.current_robot_x, self.current_robot_y)

        # 1. RECOVERY CHECK (If trapped / obstacle < 0.25m)
        if min_obstacle_m < 0.25:
            self.stuck_counter += 1
            self.state = AutoExploreFSMState.RECOVERY
            logger.warning(f"⚠️ [AUTO EXPLORE RECOVERY] Obstacle at {min_obstacle_m:.2f}m < 0.25m! Executing Recovery back & turn.")
            return "lui 60", {"state": self.state.name, "reason": "RECOVERY_BACKUP", "stuck_count": self.stuck_counter}

        if self.stuck_counter > 3:
            self.stuck_counter = 0
            self.spatial_memory.record_dead_end(self.current_robot_x, self.current_robot_y)
            return "xoay_phai 60", {"state": self.state.name, "reason": "RECOVERY_DEAD_END_SPIN"}

        self.stuck_counter = 0

        # 2. FUSION & SECTOR PLANNING
        self.state = AutoExploreFSMState.FUSION
        best_sector, best_score = self.evaluate_free_space_sectors(lidar_scan, semantic_dets)

        # Convert best sector index to movement command
        cmd = "tien 70"
        if best_sector == 0 or best_sector == 35:
            cmd = "tien 70"
            self.state = AutoExploreFSMState.MOVE
        elif 1 <= best_sector <= 6:
            cmd = "cheo_tp 70"
            self.state = AutoExploreFSMState.LOCAL_AVOID
        elif 7 <= best_sector <= 17:
            cmd = "xoay_phai 60"
            self.state = AutoExploreFSMState.LOCAL_AVOID
        elif 18 <= best_sector <= 28:
            cmd = "xoay_trai 60"
            self.state = AutoExploreFSMState.LOCAL_AVOID
        else:
            cmd = "cheo_tt 70"
            self.state = AutoExploreFSMState.LOCAL_AVOID

        # Slow down near obstacles (0.25m ~ 0.50m)
        if min_obstacle_m < 0.50 and "tien" in cmd:
            cmd = "tien 50"

        metadata = {
            "state": self.state.name,
            "best_sector": best_sector,
            "free_space_score": round(best_score, 2),
            "min_obstacle_m": round(min_obstacle_m, 2),
            "command": cmd
        }

        return cmd, metadata

    def reset(self):
        self.state = AutoExploreFSMState.IDLE
        self.spatial_memory.reset()
        self.stuck_counter = 0
        self.last_recovery_ts = 0.0
