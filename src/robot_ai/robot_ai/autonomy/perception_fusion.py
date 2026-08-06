import time
import math
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class WorldModel:
    """Unified Environmental Representation combining LiDAR, Camera Vision & Pose."""
    robot_x: float = 0.0
    robot_y: float = 0.0
    robot_yaw: float = 0.0

    min_front_dist: float = 999.0
    min_left_dist: float = 999.0
    min_right_dist: float = 999.0
    min_rear_dist: float = 999.0

    detected_person: bool = False
    person_distance: float = 0.0
    person_angle: float = 0.0

    goal_visible: bool = False
    goal_x: float = 0.0
    goal_y: float = 0.0

    corridor_detected: bool = False
    corridor_angle: float = 0.0

    confidence_score: float = 1.0
    last_update_ts: float = 0.0


class PerceptionFusionManager:
    """
    Perception Fusion Layer.
    Fuses LiDAR distances, Camera Vision Object detections, and Encoder/IMU Pose
    into a single thread-safe WorldModel instance for Local Planner consumption.
    """

    def __init__(self):
        self._world_model = WorldModel()
        self._lock = threading.Lock()

    def update_pose(self, x: float, y: float, yaw: float):
        """Update robot estimated pose."""
        with self._lock:
            self._world_model.robot_x = x
            self._world_model.robot_y = y
            self._world_model.robot_yaw = yaw
            self._world_model.last_update_ts = time.time()

    def update_lidar_summary(self, front: float, left: float, right: float, rear: float):
        """Update directional minimal distance metrics from LiDAR sectors."""
        with self._lock:
            self._world_model.min_front_dist = front
            self._world_model.min_left_dist = left
            self._world_model.min_right_dist = right
            self._world_model.min_rear_dist = rear
            self._world_model.last_update_ts = time.time()

    def update_vision_detections(self, detection_text: str):
        """Parse camera vision detections (JSON or formatted text from /detection)."""
        if not detection_text:
            return

        with self._lock:
            text_lower = detection_text.lower()
            if "person" in text_lower or "người" in text_lower:
                self._world_model.detected_person = True
            else:
                self._world_model.detected_person = False

            if "corridor" in text_lower or "hành lang" in text_lower:
                self._world_model.corridor_detected = True
            else:
                self._world_model.corridor_detected = False

            # Update overall perception confidence score
            if self._world_model.min_front_dist < 0.4:
                self._world_model.confidence_score = 0.5
            else:
                self._world_model.confidence_score = 0.95

            self._world_model.last_update_ts = time.time()

    def get_world_model(self) -> WorldModel:
        """Return a thread-safe snapshot of the current WorldModel."""
        with self._lock:
            return WorldModel(
                robot_x=self._world_model.robot_x,
                robot_y=self._world_model.robot_y,
                robot_yaw=self._world_model.robot_yaw,
                min_front_dist=self._world_model.min_front_dist,
                min_left_dist=self._world_model.min_left_dist,
                min_right_dist=self._world_model.min_right_dist,
                min_rear_dist=self._world_model.min_rear_dist,
                detected_person=self._world_model.detected_person,
                person_distance=self._world_model.person_distance,
                person_angle=self._world_model.person_angle,
                goal_visible=self._world_model.goal_visible,
                goal_x=self._world_model.goal_x,
                goal_y=self._world_model.goal_y,
                corridor_detected=self._world_model.corridor_detected,
                corridor_angle=self._world_model.corridor_angle,
                confidence_score=self._world_model.confidence_score,
                last_update_ts=self._world_model.last_update_ts
            )
