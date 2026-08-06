from enum import Enum, auto
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple


class RobotMode(Enum):
    EMERGENCY_STOP = auto()
    SAFE_MANUAL = auto()
    MANUAL = auto()
    GO_TO_GOAL = auto()
    FOLLOW_PERSON = auto()
    FOLLOW_TARGET = auto()
    PATROL = auto()
    DELIVERY = auto()
    RETURN_HOME = auto()
    AUTO_EXPLORE = auto()
    INSPECTION = auto()
    VOICE_ASSISTANT = auto()
    DOCKING = auto()
    SIMULATION = auto()


# Priority Hierarchy (Lower integer = Higher Priority)
MODE_PRIORITY: Dict[RobotMode, int] = {
    RobotMode.EMERGENCY_STOP: 1,
    RobotMode.SAFE_MANUAL: 2,
    RobotMode.MANUAL: 3,
    RobotMode.GO_TO_GOAL: 4,
    RobotMode.FOLLOW_PERSON: 5,
    RobotMode.FOLLOW_TARGET: 6,
    RobotMode.PATROL: 7,
    RobotMode.DELIVERY: 8,
    RobotMode.RETURN_HOME: 9,
    RobotMode.AUTO_EXPLORE: 10,
    RobotMode.INSPECTION: 11,
    RobotMode.VOICE_ASSISTANT: 12,
    RobotMode.DOCKING: 13,
    RobotMode.SIMULATION: 14,
}


@dataclass
class ModeContext:
    """Mode-specific execution context and parameter data."""
    target_goal_x: Optional[float] = None
    target_goal_y: Optional[float] = None
    target_person_id: Optional[str] = None
    waypoint_queue: List[Tuple[float, float]] = field(default_factory=list)
    mission_id: Optional[str] = None
    speed_scale: float = 1.0
    active_controller_source: str = "SYSTEM"


@dataclass
class ModeStatusTelemetry:
    """Thread-safe Mode Telemetry Status for Web Dashboard reporting."""
    current_mode: str = "MANUAL"
    previous_mode: str = "MANUAL"
    priority_level: int = 3
    is_active: bool = True
    active_controller: str = "MANUAL"
    elapsed_time_sec: float = 0.0
    context_info: Dict[str, Any] = field(default_factory=dict)
