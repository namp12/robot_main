import logging
from typing import Optional
from geometry_msgs.msg import Twist
from robot_ai.mode_manager.mode_types import RobotMode

logger = logging.getLogger("ModeIsolationGuard")


class ModeIsolationGuard:
    """
    Strict Mode Isolation Guard V4.0.
    1. In MANUAL/SAFE_MANUAL: Blocks 100% of autonomous planner outputs. Accepts joystick inputs.
    2. In AUTONOMOUS modes (AUTO_EXPLORE, FOLLOW_PERSON, PATROL, etc.): Blocks 100% of manual joystick inputs. Accepts planner outputs.
    """

    def filter_manual_input(self, current_mode: RobotMode, manual_cmd: Twist) -> Optional[Twist]:
        """Filter joystick inputs. Allowed ONLY in MANUAL or SAFE_MANUAL modes."""
        if current_mode in [RobotMode.MANUAL, RobotMode.SAFE_MANUAL]:
            return manual_cmd
        logger.debug(f"🛡️ [GUARD] Blocked manual joystick input while in mode '{current_mode.name}'")
        return None

    def filter_auto_input(self, current_mode: RobotMode, auto_cmd: Twist) -> Optional[Twist]:
        """Filter autonomous planner inputs. Allowed ONLY in active AUTONOMOUS modes."""
        if current_mode in [RobotMode.MANUAL, RobotMode.VOICE_ASSISTANT, RobotMode.EMERGENCY_STOP]:
            logger.debug(f"🛡️ [GUARD] Blocked auto planner output while in mode '{current_mode.name}'")
            return None
        return auto_cmd
