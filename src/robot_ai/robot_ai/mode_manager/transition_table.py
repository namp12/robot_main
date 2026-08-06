from typing import Set, Tuple
from robot_ai.mode_manager.mode_types import RobotMode, MODE_PRIORITY


class ModeTransitionValidator:
    """
    Mode Transition Table & Priority Rule Matrix.
    Validates whether transitioning between two modes is allowed.
    """

    def __init__(self):
        # Explicit Allowed Direct Transitions Set (FromMode, ToMode)
        self._allowed_transitions: Set[Tuple[RobotMode, RobotMode]] = set()
        self._build_transition_matrix()

    def _build_transition_matrix(self):
        all_modes = list(RobotMode)

        # 1. EMERGENCY_STOP can be triggered from ANY mode at any time
        for m in all_modes:
            self._allowed_transitions.add((m, RobotMode.EMERGENCY_STOP))

        # 2. Resetting from EMERGENCY_STOP is only allowed to MANUAL or SAFE_MANUAL
        self._allowed_transitions.add((RobotMode.EMERGENCY_STOP, RobotMode.MANUAL))
        self._allowed_transitions.add((RobotMode.EMERGENCY_STOP, RobotMode.SAFE_MANUAL))

        # 3. Transitions among operational modes
        operational = [m for m in all_modes if m != RobotMode.EMERGENCY_STOP]
        for m1 in operational:
            for m2 in operational:
                self._allowed_transitions.add((m1, m2))

    def is_valid_transition(self, current_mode: RobotMode, target_mode: RobotMode) -> Tuple[bool, str]:
        """Check if transition from current_mode to target_mode is valid."""
        if current_mode == target_mode:
            return True, "Same mode"

        # Higher priority override check
        current_prio = MODE_PRIORITY.get(current_mode, 99)
        target_prio = MODE_PRIORITY.get(target_mode, 99)

        # Target mode has strictly higher priority (lower integer value)
        if target_prio < current_prio:
            return True, f"Priority override ({target_mode.name} Prio {target_prio} > {current_mode.name} Prio {current_prio})"

        if (current_mode, target_mode) in self._allowed_transitions:
            return True, "Valid transition matrix entry"

        return False, f"Transition from {current_mode.name} to {target_mode.name} rejected by Transition Table"
