from typing import Optional, Tuple
from robot_ai.mode_manager.mode_types import RobotMode


class ModeApiAdapter:
    """
    Translates REST API payload requests into RobotMode switch intents.
    """

    def parse_api_request(self, payload_mode: str) -> Optional[Tuple[RobotMode, str]]:
        """Parse REST API body payload to RobotMode."""
        clean_str = payload_mode.strip().upper().replace("MODE_", "")
        for mode in RobotMode:
            if mode.name == clean_str:
                return mode, f"REST API Call: [{mode.name}]"
        return None
