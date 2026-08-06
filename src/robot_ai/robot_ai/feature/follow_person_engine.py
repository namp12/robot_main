import time
import math
import logging
from enum import Enum, auto
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("FollowPersonEngineV3")


class FollowPersonFSMState(Enum):
    IDLE = auto()
    SEARCH = auto()
    DETECT = auto()
    LOCK = auto()
    FOLLOW = auto()
    KEEP_DISTANCE = auto()
    SAFETY_STOP = auto()
    LOST = auto()
    STOP = auto()


class TargetLockManagerV3:
    """
    Manages Person Target Lock for FOLLOW_PERSON V3.
    Locks EXCLUSIVELY to ONE person tracking ID (e.g. ID = 3).
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
                    logger.info(f"🔒 [TARGET LOCK V3] Target ID {self.locked_target_id} lost > {self.lost_timeout_sec}s. Unlocking.")
                    self.locked_target_id = None
            return None

        # 1. If already locked, look for the EXACT same target ID
        if self.locked_target_id is not None:
            for person in person_detections:
                if person.get("track_id") == self.locked_target_id:
                    self.last_seen_timestamp = now
                    return person

            # Locked target missing in current frame
            if (now - self.last_seen_timestamp) > self.lost_timeout_sec:
                logger.info(f"🔒 [TARGET LOCK V3] Target ID {self.locked_target_id} disappeared > {self.lost_timeout_sec}s. Unlocking.")
                self.locked_target_id = None
            else:
                return None

        # 2. Lock first available target if none is currently locked
        if person_detections and self.locked_target_id is None:
            best_person = max(person_detections, key=lambda p: p.get("area", p.get("bbox_height", 0) * p.get("bbox_width", 0)))
            track_id = best_person.get("track_id", 3)
            self.locked_target_id = track_id
            self.last_seen_timestamp = now
            logger.info(f"🔒 [TARGET LOCK V3] Locked exclusively to Target ID: {self.locked_target_id}")
            return best_person

        return None

    def release_lock(self):
        self.locked_target_id = None
        self.last_seen_timestamp = 0.0


class DistanceEstimatorV3:
    """
    Estimates target distance using Bounding Box Height + Width + Exponential Moving Average Filter.
    Target Zone: 1.2m (Deadband: 1.0m ~ 1.4m).
    """

    def __init__(self, frame_height: int = 480, frame_width: int = 640):
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.filtered_dist: Optional[float] = None
        self.alpha = 0.35  # Low-pass filter smoothing coefficient

    def estimate_distance(self, bbox: Tuple[int, int, int, int]) -> float:
        x1, y1, x2, y2 = bbox
        bw = max(1, x2 - x1)
        bh = max(1, y2 - y1)

        height_ratio = bh / float(self.frame_height)
        width_ratio = bw / float(self.frame_width)

        # Empirical calibration for human height (~1.7m) to target ~1.2m
        raw_dist = 1.60 / (height_ratio + 0.1 * width_ratio)

        if self.filtered_dist is None:
            self.filtered_dist = raw_dist
        else:
            self.filtered_dist = (self.alpha * raw_dist) + ((1.0 - self.alpha) * self.filtered_dist)

        return round(self.filtered_dist, 2)


class FollowPersonEngine:
    """
    Commercial-Grade Behavior Engine for FOLLOW_PERSON V3 (Tracking & Distance Control Fix).
    Strictly isolated: Camera AI + YOLO11 + Person Tracker + Combined Steering/Distance PID + LiDAR Safety.
    
    Combined Motion Matrix:
    - Deadband Distance: 1.0m ~ 1.4m (Target ~1.2m)
    - Normalized Error x: error_x = (center_x - img_center) / (img_width / 2)  [-1.0 to +1.0]
    - Error Deadband: -0.15 <= error_x <= 0.15
    
    Commands:
    - Far (> 1.4m) + Left (error < -0.15) -> cheo_tt 70 (Forward + Turn Left)
    - Far (> 1.4m) + Right (error > 0.15) -> cheo_tp 70 (Forward + Turn Right)
    - Far (> 1.4m) + Center -> tien 70 (Forward Straight)
    
    - Close (< 1.0m) + Left (error < -0.15) -> cheo_st 60 (Backward + Turn Left)
    - Close (< 1.0m) + Right (error > 0.15) -> cheo_sp 60 (Backward + Turn Right)
    - Close (< 1.0m) + Center -> lui 50 (Backward Straight)
    
    - Deadband (1.0m ~ 1.4m) + Left -> trai 50 (Rotate Left in place)
    - Deadband (1.0m ~ 1.4m) + Right -> phai 50 (Rotate Right in place)
    - Deadband (1.0m ~ 1.4m) + Center -> dung (Hold Distance, Stand Still)
    """

    def __init__(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock = TargetLockManagerV3(lost_timeout_sec=5.0)
        self.distance_estimator = DistanceEstimatorV3()

        self.last_target_seen_ts: float = 0.0
        self.safety_stop_active: bool = False
        self.safety_clearance_hysteresis_m: float = 0.50

        self.filtered_error_x: float = 0.0
        self.alpha_error = 0.40  # Anti-jitter low-pass filter for steering

    def process_cycle(self, perception_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        now = time.time()
        detections = perception_data.get("detections", [])
        min_obstacle_dist = perception_data.get("min_obstacle_distance_m", 99.0)
        frame_w = perception_data.get("frame_width", 640)

        # 1. LIDAR SAFETY LAYER CHECK (Obstacle < 40 cm -> STOP IMMEDIATELY)
        if self.safety_stop_active:
            if min_obstacle_dist < self.safety_clearance_hysteresis_m:
                self.state = FollowPersonFSMState.SAFETY_STOP
                return "dung", {
                    "state": self.state.name,
                    "tracking_id": self.target_lock.locked_target_id,
                    "distance_m": 0.0,
                    "target_state": "SAFETY_STOP",
                    "current_speed": 0,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "WAITING_FOR_CLEARANCE"
                }
            else:
                self.safety_stop_active = False
                logger.info(f"🟢 [SAFETY CLEARED] Obstacle at {min_obstacle_dist:.2f}m > 0.50m. Resuming Follow.")

        if min_obstacle_dist < 0.40:
            self.state = FollowPersonFSMState.SAFETY_STOP
            self.safety_stop_active = True
            logger.warning(f"🚨 [SAFETY STOP TRIGGERED] Obstacle detected at {min_obstacle_dist:.2f}m < 0.40m! Stopping immediately.")
            return "dung", {
                "state": self.state.name,
                "tracking_id": self.target_lock.locked_target_id,
                "distance_m": 0.0,
                "target_state": "SAFETY_STOP",
                "current_speed": 0,
                "obstacle_distance_m": round(min_obstacle_dist, 2),
                "follow_state": self.state.name,
                "safety_status": "SAFETY_STOP_OBSTACLE"
            }

        # 2. TARGET LOCK & SELECTION
        locked_person = self.target_lock.update_target(detections)

        if locked_person is None:
            time_missing = (now - self.last_target_seen_ts) if self.last_target_seen_ts > 0 else 999.0

            if time_missing < 2.0:
                # < 2s -> Keep Target & Stand Still Wait
                self.state = FollowPersonFSMState.LOST
                return "dung", {
                    "state": self.state.name,
                    "tracking_id": self.target_lock.locked_target_id,
                    "target_state": "LOST_SHORT_WAIT",
                    "current_speed": 0,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "SAFE"
                }
            elif 2.0 <= time_missing <= 5.0:
                # 2~5s -> Slow Search Spin (10 deg/s)
                self.state = FollowPersonFSMState.SEARCH
                return "xoay_trai 40", {
                    "state": self.state.name,
                    "tracking_id": self.target_lock.locked_target_id,
                    "target_state": "SEARCH_SPIN",
                    "current_speed": 40,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "SAFE"
                }
            else:
                # > 5s -> Cancel Target & STOP
                self.state = FollowPersonFSMState.STOP
                self.target_lock.release_lock()
                return "dung", {
                    "state": self.state.name,
                    "tracking_id": None,
                    "target_state": "TARGET_RELEASED",
                    "current_speed": 0,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "SAFE"
                }

        self.last_target_seen_ts = now
        bbox = locked_person.get("bbox", (0, 0, 100, 100))
        center_x = (bbox[0] + bbox[2]) / 2.0
        
        # Normalized Steering Error [-1.0, 1.0]
        raw_error_x = (center_x - (frame_w / 2.0)) / (frame_w / 2.0) if frame_w > 0 else 0.0
        self.filtered_error_x = (self.alpha_error * raw_error_x) + ((1.0 - self.alpha_error) * self.filtered_error_x)

        # Distance Estimation
        estimated_dist = self.distance_estimator.estimate_distance(bbox)

        # 3. COMBINED MOTION MATRIX (Steering Error + Distance Deadband 1.0m~1.4m)
        is_left = self.filtered_error_x < -0.15
        is_right = self.filtered_error_x > 0.15
        is_center = not (is_left or is_right)

        is_far = estimated_dist > 1.40
        is_close = estimated_dist < 1.00
        is_deadband = not (is_far or is_close)

        cmd = "dung"
        target_state_str = "KEEP_DISTANCE_DEADBAND"

        if is_far:
            self.state = FollowPersonFSMState.FOLLOW
            if is_left:
                cmd = "cheo_tt 70"   # Forward + Turn Left
                target_state_str = "FORWARD_LEFT"
            elif is_right:
                cmd = "cheo_tp 70"   # Forward + Turn Right
                target_state_str = "FORWARD_RIGHT"
            else:
                cmd = "tien 70"      # Forward Straight
                target_state_str = "FORWARD_STRAIGHT"
        elif is_close:
            self.state = FollowPersonFSMState.KEEP_DISTANCE
            if is_left:
                cmd = "cheo_st 60"   # Backward + Turn Left (Vừa lùi vừa xoay trái)
                target_state_str = "BACKWARD_LEFT"
            elif is_right:
                cmd = "cheo_sp 60"   # Backward + Turn Right (Vừa lùi vừa xoay phải)
                target_state_str = "BACKWARD_RIGHT"
            else:
                cmd = "lui 50"       # Backward Straight
                target_state_str = "BACKWARD_STRAIGHT"
        else:
            # Deadband (1.0m <= dist <= 1.4m, target 1.2m): Hold distance, rotate in place if off-center
            self.state = FollowPersonFSMState.KEEP_DISTANCE
            if is_left:
                cmd = "trai 50"      # Rotate Left in place
                target_state_str = "ROTATE_LEFT_DEADBAND"
            elif is_right:
                cmd = "phai 50"      # Rotate Right in place
                target_state_str = "ROTATE_RIGHT_DEADBAND"
            else:
                cmd = "dung"         # Perfect Hold Distance (Stop)
                target_state_str = "HOLD_DISTANCE_PERFECT"

        metadata = {
            "state": self.state.name,
            "tracking_id": self.target_lock.locked_target_id,
            "distance_m": estimated_dist,
            "error_x": round(self.filtered_error_x, 2),
            "target_state": target_state_str,
            "current_speed": cmd,
            "obstacle_distance_m": round(min_obstacle_dist, 2),
            "follow_state": self.state.name,
            "safety_status": "SAFE"
        }

        return cmd, metadata

    def reset(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock.release_lock()
        self.safety_stop_active = False
        self.last_target_seen_ts = 0.0
        self.filtered_error_x = 0.0
