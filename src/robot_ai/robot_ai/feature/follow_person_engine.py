import time
import math
import logging
from enum import Enum, auto
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("FollowPersonEngineV3")


class FollowPersonFSMState(Enum):
    IDLE = auto()
    SEARCH_PERSON = auto()
    LOCK_TARGET = auto()
    FOLLOW = auto()
    KEEP_DISTANCE = auto()
    SAFETY_CHECK = auto()
    LOST_TARGET = auto()
    STOP = auto()


class TargetLockManagerV3:
    """
    Manages Person Target Lock for FOLLOW_PERSON V3.
    Locks EXCLUSIVELY to ONE person tracking ID (e.g. ID = 4).
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
            track_id = best_person.get("track_id", 4)
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
    Estimates target distance using Bounding Box Height + Width + Moving Average Filter.
    Target Zone: ~1.2m.
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

        # Empirical calibration for human height (~1.7m) to target ~1.2m
        raw_dist = 1.60 / (height_ratio + 0.1 * width_ratio)

        self.history.append(raw_dist)
        if len(self.history) > self.history_max:
            self.history.pop(0)

        smooth_dist = sum(self.history) / len(self.history)
        return round(smooth_dist, 2)


class FollowPersonEngine:
    """
    Behavior Engine for FOLLOW_PERSON V3 (KEEP DISTANCE + SAFETY STOP).
    Strictly isolated: Camera AI + YOLO11 + Person Tracker + Distance Controller + LiDAR Safety.
    
    Rules:
    - Target Distance ~ 1.2m.
      - > 1.5m -> Move Forward (0.25~0.35 m/s, `tien 70`)
      - 1.0m ~ 1.5m -> Stand Still (Hold distance, `dung`)
      - < 0.8m -> Move Backward (0.15 m/s, `lui 50`)
    - Steering: CenterX < 40% -> Turn Left; CenterX > 60% -> Turn Right; 40~60% -> Straight.
    - LiDAR Safety: Obstacle < 40cm -> STOP IMMEDIATELY (State: SAFETY_CHECK). Wait until > 50cm -> Auto Resume.
      NO Replan, NO Costmap, NO Auto Avoidance.
    - Target Lost: < 2s -> Stand & Wait; 2~5s -> Slow Search; > 5s -> Cancel Target & STOP.
    """

    def __init__(self):
        self.state = FollowPersonFSMState.IDLE
        self.target_lock = TargetLockManagerV3(lost_timeout_sec=5.0)
        self.distance_estimator = DistanceEstimatorV3()

        self.last_target_seen_ts: float = 0.0
        self.safety_stop_active: bool = False
        self.safety_clearance_hysteresis_m: float = 0.50

    def process_cycle(self, perception_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Executes one control cycle for Follow Person V3.
        Returns (command_str, metadata_dict).
        """
        now = time.time()
        detections = perception_data.get("detections", [])
        min_obstacle_dist = perception_data.get("min_obstacle_distance_m", 99.0)
        frame_w = perception_data.get("frame_width", 640)

        # 1. LIDAR SAFETY LAYER CHECK (Obstacle < 40 cm -> STOP IMMEDIATELY)
        if self.safety_stop_active:
            # Hysteresis check: Must clear > 50 cm before auto-resuming
            if min_obstacle_dist < self.safety_clearance_hysteresis_m:
                self.state = FollowPersonFSMState.SAFETY_CHECK
                logger.info(f"🛑 [SAFETY CHECK WAIT MODE] Obstacle at {min_obstacle_dist:.2f}m < 0.50m. Waiting for clearance.")
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
                logger.info(f"🟢 [SAFETY CHECK CLEARED] Obstacle cleared at {min_obstacle_dist:.2f}m > 0.50m. Auto Resuming Follow.")

        if min_obstacle_dist < 0.40:
            self.state = FollowPersonFSMState.SAFETY_CHECK
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
                self.state = FollowPersonFSMState.LOST_TARGET
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
                # 2~5s -> Slow Search Spin
                self.state = FollowPersonFSMState.SEARCH_PERSON
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
        center_x_pct = center_x / float(frame_w) if frame_w > 0 else 0.50

        # 3. DISTANCE ESTIMATION (~1.2m Target)
        estimated_dist = self.distance_estimator.estimate_distance(bbox)

        # 4. DIRECTION / STEERING DECISION (CenterX 40% ~ 60%)
        # CenterX < 40% -> Turn Left; CenterX > 60% -> Turn Right; 40~60% -> Straight
        steering_cmd = "straight"
        if center_x_pct < 0.40:
            steering_cmd = "left"
        elif center_x_pct > 0.60:
            steering_cmd = "right"

        # 5. DISTANCE CONTROL DECISION
        # > 1.5m -> Forward; 1.0 ~ 1.5m -> Hold (Stand still); < 0.8m -> Backward
        cmd = "dung"
        target_state_str = "KEEP_DISTANCE"

        if estimated_dist > 1.50:
            self.state = FollowPersonFSMState.FOLLOW
            target_state_str = "FOLLOW_FORWARD"
            if steering_cmd == "left":
                cmd = "cheo_tt 70"
            elif steering_cmd == "right":
                cmd = "cheo_tp 70"
            else:
                cmd = "tien 70"
        elif estimated_dist < 0.80:
            self.state = FollowPersonFSMState.KEEP_DISTANCE
            target_state_str = "KEEP_DISTANCE_BACKWARD"
            cmd = "lui 50"
        else:
            # 1.0m <= estimated_dist <= 1.5m (Target ~1.2m): Stand still / Turn in place to keep centered
            self.state = FollowPersonFSMState.KEEP_DISTANCE
            target_state_str = "KEEP_DISTANCE_HOLD"
            if steering_cmd == "left":
                cmd = "trai 50"
            elif steering_cmd == "right":
                cmd = "phai 50"
            else:
                cmd = "dung"

        metadata = {
            "state": self.state.name,
            "tracking_id": self.target_lock.locked_target_id,
            "distance_m": estimated_dist,
            "center_x_pct": round(center_x_pct * 100, 1),
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
