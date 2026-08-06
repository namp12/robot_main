import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any
from robot_ai.mode_manager.mode_types import RobotMode, MODE_PRIORITY


@dataclass
class ModeStatusRecord:
    current_mode: str = "MANUAL"
    previous_mode: str = "MANUAL"
    requested_mode: str = "MANUAL"
    controller_source: str = "SYSTEM"
    running_time_sec: float = 0.0
    priority_level: int = 3
    is_locked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModeStatusManager:
    """
    Tracks and formats live mode status telemetry for Web Dashboard & WebSockets.
    """

    def __init__(self, initial_mode: RobotMode = RobotMode.MANUAL):
        self._record = ModeStatusRecord(
            current_mode=initial_mode.name,
            previous_mode=initial_mode.name,
            requested_mode=initial_mode.name,
            priority_level=MODE_PRIORITY.get(initial_mode, 3)
        )
        self._mode_start_ts = time.time()
        self._lock = threading.Lock()

    def update_mode(self, new_mode: RobotMode, source: str = "SYSTEM", is_locked: bool = False):
        with self._lock:
            self._record.previous_mode = self._record.current_mode
            self._record.current_mode = new_mode.name
            self._record.requested_mode = new_mode.name
            self._record.controller_source = source
            self._record.priority_level = MODE_PRIORITY.get(new_mode, 99)
            self._record.is_locked = is_locked
            self._mode_start_ts = time.time()

    def get_status_dict(self) -> Dict[str, Any]:
        with self._lock:
            elapsed = time.time() - self._mode_start_ts
            return {
                "current_mode": self._record.current_mode,
                "previous_mode": self._record.previous_mode,
                "requested_mode": self._record.requested_mode,
                "controller_source": self._record.controller_source,
                "running_time_sec": round(elapsed, 1),
                "priority_level": self._record.priority_level,
                "is_locked": self._record.is_locked,
                "timestamp": time.time()
            }
