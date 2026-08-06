import time
import math
import logging
from enum import Enum, auto
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("FollowPersonEngineV31")


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


class TargetLockManagerV31:
    """
    Manages Person Target Lock for FOLLOW_PERSON V3.1.
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
                    logger.info(f"🔒 [TARGET LOCK V3.1] Target ID {self.locked_target_id} lost > {self.lost_timeout_sec}s. Unlocking.")
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
                logger.info(f"🔒 [TARGET LOCK V3.1] Target ID {self.locked_target_id} disappeared > {self.lost_timeout_sec}s. Unlocking.")
                self.locked_target_id = None
            else:
                return None

        # 2. Lock first available target if none is currently locked
        if person_detections and self.locked_target_id is None:
            best_person = max(person_detections, key=lambda p: p.get("area", p.get("bbox_height", 0) * p.get("bbox_width", 0)))
            track_id = best_person.get("track_id", 3)
            self.locked_target_id = track_id
            self.last_seen_timestamp = now
            logger.info(f"🔒 [TARGET LOCK V3.1] Locked exclusively to Target ID: {self.locked_target_id}")
            return best_person

        return None

    def release_lock(self):
        self.locked_target_id = None
        self.last_seen_timestamp = 0.0


class DistanceEstimatorV31:
    """
    Estimates target distance using Bounding Box Height + Width + Exponential Low-Pass Filter.
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
    Commercial-Grade Behavior Engine for FOLLOW_PERSON V3.1.
    Strictly isolated: Camera AI + YOLO11 + Person Tracker + Dual Parallel Turn/Distance PID + LiDAR Safety.
    
    Hard Speed Limit: MAX SPEED = 70 (NEVER EXCEEDS 70 IN ANY SITUATION).
    
    Rules:
    1. Turn Controller:
       - pixel_error_x = center_person - center_camera (center_camera = 320 for 640px)
       - |pixel_error_x| <= 30 px -> Straight (0 angular)
       - pixel_error_x < -30 px -> Turn Left
       - pixel_error_x > 30 px -> Turn Right
       - Priority Rule: If |pixel_error_x| > 115 px (~ angle > 20°), ONLY ROTATE IN PLACE (0 linear speed).
    
    2. Distance Controller:
       - Target Distance = 1.2m (Deadband: 1.0m ~ 1.4m -> 0 linear speed, Stand Still).
       - Distance > 1.4m -> Move Forward
       - Distance < 1.0m -> Move Backward
    
    3. Dual Parallel Steering while Backing Up:
       - While backing up (Distance < 1.0m), Turn Controller remains 100% ACTIVE.
       - Close + Left -> cheo_st (Backward + Turn Left)
       - Close + Right -> cheo_sp (Backward + Turn Right)
       - Close + Center -> lui (Backward Straight)
    
    4. Smooth Speed Scaling (Hard capped <= 70):
       - Linear Speed: Far (>2.2m) -> 70 | Mid (1.8-2.2m) -> 40 | Near (1.4-1.8m) -> 20 | Deadband (1.0-1.4m) -> 0
       - Angular Speed: Large (>115px) -> 70 | Mid (60-115px) -> 45 | Small (30-60px) -> 20 | Center (<=30px) -> 0
    """

    MAX_SPEED_CAP = 70  # ABSOLUTE HARD SPEED LIMIT

    def __init__(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock = TargetLockManagerV31(lost_timeout_sec=5.0)
        self.distance_estimator = DistanceEstimatorV31()

        self.last_target_seen_ts: float = 0.0
        self.safety_stop_active: bool = False
        self.safety_clearance_hysteresis_m: float = 0.50

        self.filtered_pixel_error: float = 0.0
        self.alpha_error = 0.40  # Anti-jitter low-pass filter

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
                # 2~5s -> Slow Search Spin (Hard capped 45)
                self.state = FollowPersonFSMState.SEARCH
                return "xoay_trai 45", {
                    "state": self.state.name,
                    "tracking_id": self.target_lock.locked_target_id,
                    "target_state": "SEARCH_SPIN",
                    "current_speed": 45,
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
        center_camera = frame_w / 2.0

        # Pixel Error & Anti-Jitter Low-Pass Filter
        raw_pixel_error = center_x - center_camera
        self.filtered_pixel_error = (self.alpha_error * raw_pixel_error) + ((1.0 - self.alpha_error) * self.filtered_pixel_error)

        # Distance Estimation
        estimated_dist = self.distance_estimator.estimate_distance(bbox)

        # 3. ANGULAR SPEED COMPUTATION (Scaled 0 -> 70 max)
        abs_err = abs(self.filtered_pixel_error)
        angular_speed = 0
        if abs_err > 115:
            angular_speed = 70  # Lệch nhiều (> 20°)
        elif abs_err > 60:
            angular_speed = 45  # Lệch vừa
        elif abs_err > 30:
            angular_speed = 20  # Lệch ít
        else:
            angular_speed = 0   # Trong deadband 30px

        angular_speed = min(self.MAX_SPEED_CAP, angular_speed)

        # 4. LINEAR SPEED COMPUTATION (Scaled 0 -> 70 max)
        linear_speed = 0
        if estimated_dist > 1.40:
            if estimated_dist > 2.20:
                linear_speed = 70
            elif estimated_dist > 1.80:
                linear_speed = 40
            else:
                linear_speed = 20
        elif estimated_dist < 1.00:
            if estimated_dist < 0.60:
                linear_speed = 50
            else:
                linear_speed = 30
        else:
            linear_speed = 0  # Target Deadband (1.0m ~ 1.4m): Stand Still

        linear_speed = min(self.MAX_SPEED_CAP, linear_speed)

        # 5. PRIORITY & DUAL PARALLEL MOTION EXECUTION
        is_left = self.filtered_pixel_error < -30
        is_right = self.filtered_pixel_error > 30
        is_large_angle = abs_err > 115  # Angle > 20°

        cmd = "dung"
        target_state_str = "HOLD_DISTANCE_PERFECT"

        # PRIORITY 1: Large Angle Deviation (> 20°) -> ONLY ROTATE IN PLACE
        if is_large_angle:
            self.state = FollowPersonFSMState.SEARCH
            cmd = f"trai {angular_speed}" if is_left else f"phai {angular_speed}"
            target_state_str = f"PRIORITY_ROTATE_{'LEFT' if is_left else 'RIGHT'}"
        else:
            # PRIORITY 2: Aligned within 20° -> DUAL PARALLEL MOTION
            if estimated_dist > 1.40:
                self.state = FollowPersonFSMState.FOLLOW
                if is_left:
                    cmd = f"cheo_tt {max(linear_speed, angular_speed)}"
                    target_state_str = "FORWARD_LEFT"
                elif is_right:
                    cmd = f"cheo_tp {max(linear_speed, angular_speed)}"
                    target_state_str = "FORWARD_RIGHT"
                else:
                    cmd = f"tien {linear_speed}"
                    target_state_str = "FORWARD_STRAIGHT"
            elif estimated_dist < 1.00:
                self.state = FollowPersonFSMState.KEEP_DISTANCE
                if is_left:
                    cmd = f"cheo_st {max(linear_speed, angular_speed)}"
                    target_state_str = "BACKWARD_LEFT"
                elif is_right:
                    cmd = f"cheo_sp {max(linear_speed, angular_speed)}"
                    target_state_str = "BACKWARD_RIGHT"
                else:
                    cmd = f"lui {linear_speed}"
                    target_state_str = "BACKWARD_STRAIGHT"
            else:
                # Deadband 1.0m ~ 1.4m (Target ~1.2m): Hold distance, rotate in place if off-center
                self.state = FollowPersonFSMState.KEEP_DISTANCE
                if is_left:
                    cmd = f"trai {angular_speed}"
                    target_state_str = "ROTATE_LEFT_DEADBAND"
                elif is_right:
                    cmd = f"phai {angular_speed}"
                    target_state_str = "ROTATE_RIGHT_DEADBAND"
                else:
                    cmd = "dung"
                    target_state_str = "HOLD_DISTANCE_PERFECT"

        # 6. HARD SPEED CAP SANITY CHECK (NEVER EXCEED 70)
        parts = cmd.split()
        if len(parts) > 1:
            try:
                spd_val = min(self.MAX_SPEED_CAP, int(parts[1]))
                cmd = f"{parts[0]} {spd_val}"
            except Exception:
                pass

        metadata = {
            "state": self.state.name,
            "tracking_id": self.target_lock.locked_target_id,
            "distance_m": estimated_dist,
            "pixel_error_x": round(self.filtered_pixel_error, 1),
            "target_state": target_state_str,
            "current_speed": cmd,
            "max_speed_cap": self.MAX_SPEED_CAP,
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
        self.filtered_pixel_error = 0.0
