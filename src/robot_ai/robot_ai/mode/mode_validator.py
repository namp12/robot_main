from typing import Tuple
from robot_ai.mode_manager.mode_types import RobotMode


class ModeValidator:
    """Validates pre-conditions before allowing mode transitions."""

    def validate_mode_switch(self, target_mode: RobotMode, sensor_ok: bool = True) -> Tuple[bool, str]:
        """Check if target mode preconditions are satisfied."""
        if target_mode == RobotMode.EMERGENCY_STOP:
            return True, "Emergency Stop is always valid"

        if target_mode == RobotMode.FOLLOW_PERSON and not sensor_ok:
            return False, "Camera AI sensor unavailable for FOLLOW_PERSON mode"

        return True, "Preconditions validated OK"
