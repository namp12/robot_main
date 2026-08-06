from typing import Optional, Tuple, Dict
from robot_ai.mode_manager.mode_types import RobotMode


class ModeHotkeyAdapter:
    """
    Translates keyboard shortcut hotkeys into RobotMode switch intents.
    """

    def __init__(self):
        self._hotkey_map: Dict[str, RobotMode] = {
            "ESC": RobotMode.EMERGENCY_STOP,
            "F1": RobotMode.MANUAL,
            "F2": RobotMode.SAFE_MANUAL,
            "F3": RobotMode.AUTO_EXPLORE,
            "F4": RobotMode.GO_TO_GOAL,
            "F5": RobotMode.FOLLOW_PERSON,
            "F6": RobotMode.FOLLOW_TARGET,
            "F7": RobotMode.PATROL,
            "F8": RobotMode.DELIVERY,
            "F9": RobotMode.RETURN_HOME,
            "F10": RobotMode.VOICE_ASSISTANT,
            "F11": RobotMode.INSPECTION,
            "F12": RobotMode.DOCKING,
        }

    def parse_hotkey(self, key_name: str) -> Optional[Tuple[RobotMode, str]]:
        """Parse key combination string for mode switch intent."""
        clean_key = key_name.strip().upper()
        if clean_key in self._hotkey_map:
            mode = self._hotkey_map[clean_key]
            return mode, f"Hotkey Shortcut Triggered: [{clean_key}]"

        return None
