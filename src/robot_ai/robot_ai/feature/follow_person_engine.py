import time
import math
import logging
from enum import Enum, auto
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("FollowPersonEngine")


class FollowPersonFSMState(Enum):
    IDLE = auto()
    SEARCH = auto()
    DETECT = auto()
    LOCK = auto()
    FOLLOW = auto()
    SAFETY_STOP = auto()
    LOST = auto()
    STOP = auto()


class TargetLockManager:
    """
    Manages Person Target Lock with Multi-Object Tracking ID persistence.
    Will NOT switch targets automatically unless target is lost for > 5.0 seconds.
    """

    def __init__(self, lost_timeout_sec: float = 5.0):
        self.locked_target_id: Optional[int] = None
        self.last_seen_timestamp: float = 0.0
        self.lost_timeout_sec = lost_timeout_sec

    def update_target(self, detections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        now = time.time()
        person_detections = [d for d in detections if d.get("label", "").lower() in ["person", "người", "user"]]

        if not person_detections:
            if self.locked_target_id is not None:
                if (now - self.last_seen_timestamp) > self.lost_timeout_sec:
                    logger.info(f"🔒 [TARGET LOCK] Target ID {self.locked_target_id} lost for > {self.lost_timeout_sec}s. Releasing target lock.")
                    self.locked_target_id = None
            return None

        # If already locked, look for the same target ID
        if self.locked_target_id is not None:
            for person in person_detections:
                if person.get("track_id") == self.locked_target_id:
                    self.last_seen_timestamp = now
                    return person

            # Locked target missing in current frame
            if (now - self.last_seen_timestamp) > self.lost_timeout_sec:
                logger.info(f"🔒 [TARGET LOCK] Locked Target ID {self.locked_target_id} disappeared > {self.lost_timeout_sec}s. Unlocking.")
                self.locked_target_id = None
            else:
                return None

        # Lock first available target if none is locked
        if person_detections and self.locked_target_id is None:
            best_person = max(person_detections, key=lambda p: p.get("area", p.get("bbox_height", 0) * p.get("bbox_width", 0)))
            track_id = best_person.get("track_id", 1)
            self.locked_target_id = track_id
            self.last_seen_timestamp = now
            logger.info(f"🔒 [TARGET LOCK] Locked onto new Person Target ID: {self.locked_target_id}")
            return best_person

        return None

    def release_lock(self):
        self.locked_target_id = None
        self.last_seen_timestamp = 0.0


class DistanceEstimatorV2:
    """
    Estimates target distance using Bounding Box Height + Width + Historical Moving Average Filter.
    """

    def __init__(self, frame_height: int = 480, frame_width: int = 640):
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.history: List[float] = []
        self.history_max = 5

    def estimate_distance(self, bbox: Tuple[int, int, int, int]) -> float:
        x1, y1, x2, y2 = bbox
        bw = max(1, x2 - x1)
        bh = max(1, y2 - y1)

        height_ratio = bh / float(self.frame_height)
        width_ratio = bw / float(self.frame_width)

        # Empirical focal length calibration model for human height (~1.7m)
        raw_dist = 1.60 / (height_ratio + 0.1 * width_ratio)

        # Historical moving average smoothing
        self.history.append(raw_dist)
        if len(self.history) > self.history_max:
            self.history.pop(0)

        smooth_dist = sum(self.history) / len(self.history)
        return round(smooth_dist, 2)


class FollowPersonEngine:
    """
    Behavior Engine for FOLLOW_PERSON V2.
    Strictly isolated: Camera AI + YOLO11 + Person Tracker + Safety Controller.
    LiDAR Navigation is OFF; LiDAR acts exclusively as a Safety Stop layer (< 0.40m -> STOP).
    """

    def __init__(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock = TargetLockManager(lost_timeout_sec=5.0)
        self.distance_estimator = DistanceEstimatorV2()

        self.last_target_seen_ts: float = 0.0
        self.safety_stop_active: bool = False

        # PID parameters
        self.kp_heading = 1.2
        self.kp_distance = 0.8

    def process_cycle(self, perception_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Executes one control cycle for Follow Person V2.
        Returns (command_str, metadata_dict).
        """
        now = time.time()
        detections = perception_data.get("detections", [])
        min_obstacle_dist = perception_data.get("min_obstacle_distance_m", 99.0)

        # 1. LIDAR SAFETY LAYER CHECK (Obstacle < 0.40m -> Immediate STOP)
        if min_obstacle_dist < 0.40:
            self.state = FollowPersonFSMState.SAFETY_STOP
            self.safety_stop_active = True
            logger.warning(f"🚨 [FOLLOW SAFETY STOP] Obstacle detected at {min_obstacle_dist:.2f}m < 0.40m! Safety STOP active.")
            return "dung", {"state": self.state.name, "reason": "SAFETY_OBSTACLE_TOO_CLOSE", "speed": 0}

        self.safety_stop_active = False

        # 2. TARGET LOCK & SELECTION
        locked_person = self.target_lock.update_target(detections)

        if locked_person is None:
            # Handle Lost Target timing
            if self.state in [FollowPersonFSMState.FOLLOW, FollowPersonFSMState.LOCK]:
                self.state = FollowPersonFSMState.LOST

            if self.last_target_seen_ts > 0 and (now - self.last_target_seen_ts) < 2.0:
                self.state = FollowPersonFSMState.SEARCH
                return "xoay_trai 40", {"state": self.state.name, "reason": "SEARCHING_LOST_TARGET_LIGHT_SPIN"}
            elif self.last_target_seen_ts > 0 and (now - self.last_target_seen_ts) > 5.0:
                self.state = FollowPersonFSMState.STOP
                self.target_lock.release_lock()
                return "dung", {"state": self.state.name, "reason": "TARGET_LOST_TIMEOUT_RELEASED"}
            else:
                self.state = FollowPersonFSMState.SEARCH
                return "dung", {"state": self.state.name, "reason": "SEARCHING_TARGET"}

        self.last_target_seen_ts = now
        self.state = FollowPersonFSMState.FOLLOW

        # 3. STEERING & HEADING COMPUTATION
        bbox = locked_person.get("bbox", (0, 0, 100, 100))
        center_x = (bbox[0] + bbox[2]) / 2.0
        frame_w = perception_data.get("frame_width", 640)
        error_x = (center_x - (frame_w / 2.0)) / (frame_w / 2.0)  # Normalized [-1.0, 1.0]

        # 4. DISTANCE ESTIMATION
        estimated_dist = self.distance_estimator.estimate_distance(bbox)

        # 5. DISTANCE CONTROL DECISION (0.8m ~ 1.5m Target Zone)
        cmd = "dung"
        if estimated_dist > 1.50:
            # Target far (> 1.5m) -> Move Forward Slow
            cmd = "tien 60"
        elif estimated_dist < 0.80:
            # Target too close (< 0.8m) -> Move Backward Slow
            cmd = "lui 50"
        else:
            # Target in optimal range (1.0m - 1.5m) -> Hold Distance
            if abs(error_x) > 0.20:
                cmd = "trai 50" if error_x < 0 else "phai 50"
            else:
                cmd = "dung"

        # Apply steering override if center deviation is high
        if abs(error_x) > 0.25 and cmd in ["tien 60", "dung"]:
            cmd = "trai 50" if error_x < 0 else "phai 50"

        metadata = {
            "state": self.state.name,
            "target_id": self.target_lock.locked_target_id,
            "estimated_distance_m": estimated_dist,
            "error_x": round(error_x, 2),
            "command": cmd
        }

        return cmd, metadata

    def reset(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock.release_lock()
        self.safety_stop_active = False
        self.last_target_seen_ts = 0.0
