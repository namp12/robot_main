import time
import threading
from typing import Tuple, Dict, Any, Optional
from geometry_msgs.msg import Twist

from robot_ai.mode_manager.mode_types import RobotMode, MODE_PRIORITY, ModeContext, ModeStatusTelemetry
from robot_ai.mode_manager.transition_table import ModeTransitionValidator
from robot_ai.mode_manager.mode_events import ModeEventEngine, ModeEventType


class MultiModeManager:
    """
    Multi-Mode Manager Core Coordinator.
    Enforces Single Control Source Authority: At any given moment, ONLY ONE Mode
    is permitted to drive the robot via /cmd_vel.
    """

    def __init__(self, initial_mode: RobotMode = RobotMode.MANUAL):
        self._current_mode = initial_mode
        self._previous_mode = initial_mode
        self._mode_start_ts = time.time()
        self._is_paused = False

        self.validator = ModeTransitionValidator()
        self.event_engine = ModeEventEngine()
        self.context = ModeContext()

        self._lock = threading.Lock()

    def switch_mode(self, target_mode: RobotMode, context_data: Optional[ModeContext] = None) -> Tuple[bool, str]:
        """Switch to a new target mode if transition is valid and authorized by priority rules."""
        with self._lock:
            valid, reason = self.validator.is_valid_transition(self._current_mode, target_mode)
            if not valid:
                return False, reason

            prev = self._current_mode
            self._previous_mode = prev
            self._current_mode = target_mode
            self._mode_start_ts = time.time()
            self._is_paused = False

            if context_data is not None:
                self.context = context_data

        # Dispatch event asynchronously
        self.event_engine.dispatch_event(
            ModeEventType.MODE_CHANGED,
            {"from_mode": prev.name, "to_mode": target_mode.name, "reason": reason}
        )

        return True, f"Successfully switched mode: {prev.name} -> {target_mode.name}"

    def trigger_emergency_stop(self) -> Tuple[bool, str]:
        """Trigger EMERGENCY_STOP mode with highest priority override."""
        return self.switch_mode(RobotMode.EMERGENCY_STOP)

    def reset_emergency_stop(self) -> Tuple[bool, str]:
        """Reset EMERGENCY_STOP mode back to MANUAL."""
        with self._lock:
            if self._current_mode != RobotMode.EMERGENCY_STOP:
                return False, "Not in EMERGENCY_STOP mode"
        return self.switch_mode(RobotMode.MANUAL)

    def pause_current_mode(self) -> bool:
        """Pause execution of the current mode."""
        with self._lock:
            if not self._is_paused:
                self._is_paused = True
                self.event_engine.dispatch_event(ModeEventType.MODE_PAUSED, {"mode": self._current_mode.name})
                return True
        return False

    def resume_current_mode(self) -> bool:
        """Resume execution of the current mode."""
        with self._lock:
            if self._is_paused:
                self._is_paused = False
                self.event_engine.dispatch_event(ModeEventType.MODE_RESUMED, {"mode": self._current_mode.name})
                return True
        return False

    def filter_cmd_vel(self, source_mode: RobotMode, input_twist: Twist) -> Optional[Twist]:
        """
        Mode Multiplexer (Mux) Filter:
        Only allows Twist messages from the currently active mode to pass through to /cmd_vel.
        """
        with self._lock:
            if self._current_mode == RobotMode.EMERGENCY_STOP:
                # Emergency Stop: Return Zero Twist
                stop_cmd = Twist()
                return stop_cmd

            if self._is_paused:
                stop_cmd = Twist()
                return stop_cmd

            if source_mode == self._current_mode:
                return input_twist

        return None

    def get_status_telemetry(self) -> ModeStatusTelemetry:
        """Return thread-safe snapshot telemetry of current mode status."""
        with self._lock:
            curr = self._current_mode
            prev = self._previous_mode
            elapsed = time.time() - self._mode_start_ts
            paused = self._is_paused

        return ModeStatusTelemetry(
            current_mode=curr.name,
            previous_mode=prev.name,
            priority_level=MODE_PRIORITY.get(curr, 99),
            is_active=not paused,
            active_controller=curr.name,
            elapsed_time_sec=round(elapsed, 1),
            context_info={
                "speed_scale": self.context.speed_scale,
                "paused": paused
            }
        )
