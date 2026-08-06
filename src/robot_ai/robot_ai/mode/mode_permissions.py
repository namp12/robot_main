from typing import Tuple
from robot_ai.mode_manager.mode_types import RobotMode, MODE_PRIORITY


class ModePermissionChecker:
    """
    Permission Checker: Validates whether a mode switch request from a specific source
    is permitted given the active mode and lock status.
    """

    def check_permission(
        self,
        current_mode: RobotMode,
        target_mode: RobotMode,
        source: str = "SYSTEM",
        is_locked: bool = False
    ) -> Tuple[bool, str]:
        """Check if source has permission to switch mode."""
        if target_mode == RobotMode.EMERGENCY_STOP:
            return True, "Emergency Stop is always permitted"

        if is_locked and current_mode != target_mode:
            return False, f"Permission denied: Active mode {current_mode.name} is locked"

        curr_prio = MODE_PRIORITY.get(current_mode, 99)
        target_prio = MODE_PRIORITY.get(target_mode, 99)

        if target_prio < curr_prio:
            return True, f"Permission granted: Higher priority override ({target_mode.name} > {current_mode.name})"

        return True, "Permission granted"
