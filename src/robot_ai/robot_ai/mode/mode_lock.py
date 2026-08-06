import time
import threading
from typing import Tuple, Optional
from robot_ai.mode_manager.mode_types import RobotMode


class ModeLock:
    """
    Mode Lock Manager. Prevents unauthorized mode preemption while a critical mission
    (e.g., Delivery or Docking) is actively locked.
    EMERGENCY_STOP is always permitted to override any active lock.
    """

    def __init__(self):
        self._is_locked = False
        self._locked_mode: Optional[RobotMode] = None
        self._lock_owner: str = ""
        self._lock_ts: float = 0.0
        self._lock = threading.Lock()

    def acquire_lock(self, mode: RobotMode, owner: str) -> bool:
        """Lock current mode to prevent preemption."""
        with self._lock:
            if self._is_locked and self._locked_mode != mode:
                return False
            self._is_locked = True
            self._locked_mode = mode
            self._lock_owner = owner
            self._lock_ts = time.time()
            return True

    def release_lock(self, owner: str = "") -> bool:
        """Release current mode lock."""
        with self._lock:
            if not self._is_locked:
                return True
            self._is_locked = False
            self._locked_mode = None
            self._lock_owner = ""
            return True

    def can_transition(self, current_mode: RobotMode, target_mode: RobotMode) -> Tuple[bool, str]:
        """Check if lock allows transition to target_mode."""
        if target_mode == RobotMode.EMERGENCY_STOP:
            return True, "Emergency Stop overrides lock"

        with self._lock:
            if not self._is_locked:
                return True, "No active lock"
            if target_mode == self._locked_mode:
                return True, "Target mode matches locked mode"

            return False, f"Mode locked by [{self._locked_mode.name}] owned by [{self._lock_owner}]"
