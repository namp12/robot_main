from enum import Enum, auto
import time
import threading
from typing import Optional


class RobotState(Enum):
    IDLE = auto()
    EXPLORE = auto()
    MOVE_FORWARD = auto()
    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    FOLLOW_CORRIDOR = auto()
    AVOID_OBSTACLE = auto()
    RECOVERY = auto()
    SEARCH_GOAL = auto()
    REACH_GOAL = auto()
    EMERGENCY_STOP = auto()


class BehaviorManager:
    """
    Priority-based Behavior Coordinator and Hierarchical Finite State Machine.
    Priorities:
    EMERGENCY_STOP > HEALTH_FAILURE > RECOVERY > AVOID_OBSTACLE > GOAL_NAV > CORRIDOR_FOLLOW > EXPLORE > IDLE
    """

    def __init__(self):
        self._current_state = RobotState.IDLE
        self._previous_state = RobotState.IDLE
        self._state_start_ts = time.time()
        self._lock = threading.Lock()

        self._emergency_stop_triggered = False
        self._health_failure_triggered = False
        self._recovery_retry_count = 0
        self.max_recovery_retries = 5

    def set_state(self, new_state: RobotState) -> bool:
        """Attempt to transition to a new state while honoring priority constraints."""
        with self._lock:
            if self._current_state == RobotState.EMERGENCY_STOP and new_state != RobotState.IDLE:
                return False  # Emergency stop overrides everything until reset

            if self._current_state != new_state:
                self._previous_state = self._current_state
                self._current_state = new_state
                self._state_start_ts = time.time()
                return True
            return False

    def trigger_emergency_stop(self):
        """Force emergency stop state immediately."""
        with self._lock:
            self._emergency_stop_triggered = True
            self._previous_state = self._current_state
            self._current_state = RobotState.EMERGENCY_STOP
            self._state_start_ts = time.time()

    def reset_emergency_stop(self):
        """Reset emergency stop state to IDLE."""
        with self._lock:
            self._emergency_stop_triggered = False
            self._previous_state = self._current_state
            self._current_state = RobotState.IDLE
            self._recovery_retry_count = 0
            self._state_start_ts = time.time()

    def get_state(self) -> RobotState:
        """Return current state."""
        with self._lock:
            return self._current_state

    def get_state_duration(self) -> float:
        """Return elapsed duration in current state (seconds)."""
        with self._lock:
            return time.time() - self._state_start_ts

    def increment_recovery_count(self) -> int:
        """Increment and return recovery attempt count."""
        with self._lock:
            self._recovery_retry_count += 1
            if self._recovery_retry_count > self.max_recovery_retries:
                self._emergency_stop_triggered = True
                self._current_state = RobotState.EMERGENCY_STOP
            return self._recovery_retry_count

    def reset_recovery_count(self):
        """Reset recovery attempt counter."""
        with self._lock:
            self._recovery_retry_count = 0
