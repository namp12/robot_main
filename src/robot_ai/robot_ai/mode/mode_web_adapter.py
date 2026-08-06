from typing import Optional, Tuple
from robot_ai.mode_manager.mode_types import RobotMode


class ModeWebAdapter:
    """
    Translates Web Dashboard Quick Mode Panel clicks into RobotMode switch intents.
    """

    def parse_web_request(self, mode_str: str) -> Optional[Tuple[RobotMode, str]]:
        """Parse web payload mode string to RobotMode enum."""
        clean_str = mode_str.strip().upper().replace("MODE_", "")
        for mode in RobotMode:
            if mode.name == clean_str:
                return mode, f"Web Panel 1-Click Action: [{mode.name}]"
        return None
