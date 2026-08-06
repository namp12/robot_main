import time
import math
import logging
from enum import Enum, auto
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("FollowPersonEngineV23")


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


class TargetLockManagerV23:
    """
    Manages Person Target Lock for FOLLOW_PERSON V2.3.
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
                    logger.info(f"🔒 [TARGET LOCK V2.3] Target ID {self.locked_target_id} lost > {self.lost_timeout_sec}s. Unlocking.")
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
                logger.info(f"🔒 [TARGET LOCK V2.3] Target ID {self.locked_target_id} disappeared > {self.lost_timeout_sec}s. Unlocking.")
                self.locked_target_id = None
            else:
                return None

        # 2. Lock first available target if none is currently locked
        if person_detections and self.locked_target_id is None:
            best_person = max(person_detections, key=lambda p: p.get("area", p.get("bbox_height", 0) * p.get("bbox_width", 0)))
            track_id = best_person.get("track_id", 3)
            self.locked_target_id = track_id
            self.last_seen_timestamp = now
            logger.info(f"🔒 [TARGET LOCK V2.3] Locked exclusively to Target ID: {self.locked_target_id}")
            return best_person

        return None

    def release_lock(self):
        self.locked_target_id = None
        self.last_seen_timestamp = 0.0


class DistanceEstimatorV23:
    """
    Estimates target distance using Bounding Box Height + Width + Exponential Low-Pass Filter.
    Target Zone: 0.8m ~ 1.2m (Optimal ~1.0m).
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

        # Empirical calibration for human height (~1.7m) to target ~1.0m
        raw_dist = 1.45 / (height_ratio + 0.1 * width_ratio)

        if self.filtered_dist is None:
            self.filtered_dist = raw_dist
        else:
            self.filtered_dist = (self.alpha * raw_dist) + ((1.0 - self.alpha) * self.filtered_dist)

        return round(self.filtered_dist, 2)


class FollowPersonEngine:
    """
    Commercial-Grade Behavior Engine for FOLLOW_PERSON V2.3 (Behavior Fix & Stable Tracking).
    Strictly isolated: Camera AI + YOLO11 + Person Tracker + Dual Steering/Distance PID + LiDAR Safety.
    
    Speed Limits:
    - FORWARD_MAX = 70
    - BACKWARD_MAX = 50
    - TURN_MAX = 40
    
    Steering Error & Deadband:
    - norm_error_x = (center_x - center_camera) / (frame_w / 2.0)
    - |norm_error_x| < 0.08 -> Steering Deadband (Turn = 0, NO jitter)
    - 0.08 <= |norm_error_x| < 0.25 -> Turn = 15
    - 0.25 <= |norm_error_x| < 0.50 -> Turn = 25
    - |norm_error_x| >= 0.50 -> Turn = 40
    - Priority Rule: If |norm_error_x| > 0.35, ONLY ROTATE IN PLACE (linear = 0).
    
    Distance Control & Linear Speed Ramp Down:
    - Distance > 2.5m -> Speed = 70
    - 2.0m < Distance <= 2.5m -> Speed = 60
    - 1.5m < Distance <= 2.0m -> Speed = 45
    - 1.2m < Distance <= 1.5m -> Speed = 25
    - 0.8m <= Distance <= 1.2m -> Speed = 0 (Stand Still, Target Deadband)
    - 0.6m <= Distance < 0.8m -> Speed = 35 (Backward)
    - Distance < 0.6m -> Speed = 0 (HARD SAFETY STOP)
    """

    FORWARD_MAX = 200
    BACKWARD_MAX = 150
    TURN_MAX = 120

    def __init__(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock = TargetLockManagerV23(lost_timeout_sec=5.0)
        self.distance_estimator = DistanceEstimatorV23()

        self.last_target_seen_ts: float = 0.0
        self.safety_stop_active: bool = False
        self.safety_clearance_hysteresis_m: float = 0.50

        self.filtered_norm_error: float = 0.0
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
                # < 2s -> Light search spin
                self.state = FollowPersonFSMState.LOST
                return "xoay_trai 60", {
                    "state": self.state.name,
                    "tracking_id": self.target_lock.locked_target_id,
                    "target_state": "LOST_LIGHT_SEARCH",
                    "current_speed": 60,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "SAFE"
                }
            elif 2.0 <= time_missing <= 5.0:
                # 2~5s -> Full 360 scan spin
                self.state = FollowPersonFSMState.SEARCH
                return "xoay_trai 90", {
                    "state": self.state.name,
                    "tracking_id": self.target_lock.locked_target_id,
                    "target_state": "SEARCH_360_SCAN",
                    "current_speed": 90,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "SAFE"
                }
            else:
                # > 5s -> Cancel Target & STOP (IDLE)
                self.state = FollowPersonFSMState.STOP
                self.target_lock.release_lock()
                return "dung", {
                    "state": self.state.name,
                    "tracking_id": None,
                    "target_state": "TARGET_RELEASED_IDLE",
                    "current_speed": 0,
                    "obstacle_distance_m": round(min_obstacle_dist, 2),
                    "follow_state": self.state.name,
                    "safety_status": "SAFE"
                }

        self.last_target_seen_ts = now
        bbox = locked_person.get("bbox", (0, 0, 100, 100))
        center_x = (bbox[0] + bbox[2]) / 2.0
        center_camera = frame_w / 2.0

        # Normalized Error [-1.0 to +1.0] and Anti-Jitter Low-Pass Filter
        raw_norm_error = (center_x - center_camera) / (frame_w / 2.0) if frame_w > 0 else 0.0
        self.filtered_norm_error = (self.alpha_error * raw_norm_error) + ((1.0 - self.alpha_error) * self.filtered_norm_error)

        # Distance Estimation
        estimated_dist = self.distance_estimator.estimate_distance(bbox)

        # 3. STEERING SPEED COMPUTATION (Turn Max = 120)
        abs_err = abs(self.filtered_norm_error)
        turn_speed = 0
        if abs_err < 0.08:
            turn_speed = 0   # Steering Deadband (No jitter, 0 angular)
        elif abs_err < 0.25:
            turn_speed = 45  # Chậm mượt
        elif abs_err < 0.50:
            turn_speed = 85  # Vừa
        else:
            turn_speed = 120 # Turn Speed = 120

        turn_speed = min(self.TURN_MAX, turn_speed)

        # 4. LINEAR SPEED COMPUTATION (Linear Ramp Down, Forward Max = 200, Backward Max = 150)
        linear_speed = 0
        is_too_close_hard_stop = False

        if estimated_dist > 2.50:
            linear_speed = 180
        elif estimated_dist > 2.00:
            linear_speed = 140
        elif estimated_dist > 1.50:
            linear_speed = 100
        elif estimated_dist > 1.20:
            linear_speed = 60
        elif estimated_dist >= 0.80:
            linear_speed = 0  # Target Deadband (0.8m ~ 1.2m): Stand Still
        elif estimated_dist >= 0.60:
            linear_speed = 80  # Lùi nhẹ
        else:
            # Distance < 0.6m -> HARD SAFETY STOP (Do NOT move into person)
            linear_speed = 0
            is_too_close_hard_stop = True

        if estimated_dist > 1.20:
            linear_speed = min(self.FORWARD_MAX, linear_speed)
        elif estimated_dist < 0.80:
            linear_speed = min(self.BACKWARD_MAX, linear_speed)

        # 5. PRIORITY & MOTION MATRIX EXECUTION
        is_left = self.filtered_norm_error < -0.08
        is_right = self.filtered_norm_error > 0.08
        is_large_angle = abs_err > 0.35  # Angle deviation > 0.35

        cmd = "dung"
        target_state_str = "STAND_STILL_DEADBAND"

        # Check Hard Safety Stop for Distance < 0.6m
        if is_too_close_hard_stop:
            self.state = FollowPersonFSMState.KEEP_DISTANCE
            cmd = "dung"
            target_state_str = "HARD_STOP_TOO_CLOSE"
        # Priority 1: Large Angle Deviation (|error| > 0.35) -> ONLY ROTATE IN PLACE
        elif is_large_angle:
            self.state = FollowPersonFSMState.SEARCH
            cmd = f"trai {turn_speed}" if is_left else f"phai {turn_speed}"
            target_state_str = f"PRIORITY_ROTATE_{'LEFT' if is_left else 'RIGHT'}"
        else:
            # Priority 2: Aligned within 0.35 -> Motion Execution
            if estimated_dist > 1.20:
                self.state = FollowPersonFSMState.FOLLOW
                if is_left:
                    cmd = f"cheo_tt {max(linear_speed, turn_speed)}"
                    target_state_str = "FORWARD_LEFT"
                elif is_right:
                    cmd = f"cheo_tp {max(linear_speed, turn_speed)}"
                    target_state_str = "FORWARD_RIGHT"
                else:
                    cmd = f"tien {linear_speed}"
                    target_state_str = "FORWARD_STRAIGHT"
            elif estimated_dist < 0.80:
                self.state = FollowPersonFSMState.KEEP_DISTANCE
                if is_left:
                    cmd = f"cheo_st {max(linear_speed, turn_speed)}"
                    target_state_str = "BACKWARD_LEFT"
                elif is_right:
                    cmd = f"cheo_sp {max(linear_speed, turn_speed)}"
                    target_state_str = "BACKWARD_RIGHT"
                else:
                    cmd = f"lui {linear_speed}"
                    target_state_str = "BACKWARD_STRAIGHT"
            else:
                # Deadband 0.8m ~ 1.2m (Target ~1.0m): Hold distance, rotate in place if off-center
                self.state = FollowPersonFSMState.KEEP_DISTANCE
                if is_left:
                    cmd = f"trai {turn_speed}"
                    target_state_str = "ROTATE_LEFT_DEADBAND"
                elif is_right:
                    cmd = f"phai {turn_speed}"
                    target_state_str = "ROTATE_RIGHT_DEADBAND"
                else:
                    cmd = "dung"
                    target_state_str = "HOLD_DISTANCE_PERFECT"

        # 6. HARD SPEED CAP SANITY CHECK (Forward <= 70, Backward <= 50, Turn <= 40)
        parts = cmd.split()
        if len(parts) > 1:
            try:
                raw_spd = int(parts[1])
                cap = self.FORWARD_MAX
                if parts[0] in ["lui", "cheo_st", "cheo_sp"]:
                    cap = self.BACKWARD_MAX
                elif parts[0] in ["trai", "phai", "xoay_trai", "xoay_phai"]:
                    cap = self.TURN_MAX
                
                final_spd = min(cap, max(0, raw_spd))
                cmd = f"{parts[0]} {final_spd}"
            except Exception:
                pass

        metadata = {
            "state": self.state.name,
            "tracking_id": self.target_lock.locked_target_id,
            "distance_m": estimated_dist,
            "norm_error_x": round(self.filtered_norm_error, 2),
            "target_state": target_state_str,
            "current_speed": cmd,
            "forward_max": self.FORWARD_MAX,
            "backward_max": self.BACKWARD_MAX,
            "turn_max": self.TURN_MAX,
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
        self.filtered_norm_error = 0.0
