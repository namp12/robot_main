from typing import Optional
from robot_ai.mode_manager.mode_types import RobotMode
from robot_ai.preset.preset_registry import PRESET_DEFINITIONS


class PresetMapper:
    """Bi-directional mapping between Preset Number (1-14) and RobotMode."""

    @staticmethod
    def preset_to_mode(preset_id: int) -> Optional[RobotMode]:
        defn = PRESET_DEFINITIONS.get(preset_id)
        return defn.target_mode if defn else None

    @staticmethod
    def mode_to_preset(mode: RobotMode) -> Optional[int]:
        for pid, defn in PRESET_DEFINITIONS.items():
            if defn.target_mode == mode:
                return pid
        return None
