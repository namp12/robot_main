from dataclasses import dataclass
from typing import Dict
from robot_ai.mode_manager.mode_types import RobotMode


@dataclass
class ModeProfile:
    max_linear_speed: float = 0.35
    max_angular_speed: float = 0.60
    safety_distance_meter: float = 0.35
    camera_fps: int = 15
    enable_lidar: bool = True


DEFAULT_PROFILES: Dict[RobotMode, ModeProfile] = {
    RobotMode.EMERGENCY_STOP: ModeProfile(max_linear_speed=0.0, max_angular_speed=0.0),
    RobotMode.SAFE_MANUAL: ModeProfile(max_linear_speed=0.30, max_angular_speed=0.50, safety_distance_meter=0.30),
    RobotMode.MANUAL: ModeProfile(max_linear_speed=0.40, max_angular_speed=0.65),
    RobotMode.GO_TO_GOAL: ModeProfile(max_linear_speed=0.35, max_angular_speed=0.60),
    RobotMode.FOLLOW_PERSON: ModeProfile(max_linear_speed=0.25, max_angular_speed=0.45, safety_distance_meter=0.80),
    RobotMode.PATROL: ModeProfile(max_linear_speed=0.30, max_angular_speed=0.50),
    RobotMode.DELIVERY: ModeProfile(max_linear_speed=0.35, max_angular_speed=0.55),
    RobotMode.AUTO_EXPLORE: ModeProfile(max_linear_speed=0.35, max_angular_speed=0.60),
    RobotMode.INSPECTION: ModeProfile(max_linear_speed=0.15, max_angular_speed=0.30, camera_fps=30),
    RobotMode.VOICE_ASSISTANT: ModeProfile(max_linear_speed=0.0, max_angular_speed=0.0),
    RobotMode.SIMULATION: ModeProfile(max_linear_speed=0.35, max_angular_speed=0.60),
}


class ModeProfileManager:
    """Manages mode-specific execution profiles."""
    def get_profile(self, mode: RobotMode) -> ModeProfile:
        return DEFAULT_PROFILES.get(mode, ModeProfile())
