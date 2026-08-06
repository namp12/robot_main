import time
import threading
from typing import Tuple, Optional
from robot_ai.mode_manager.mode_types import RobotMode
from robot_ai.mode_manager.mode_manager import MultiModeManager
from robot_ai.preset.preset_mapping import PresetMapper
from robot_ai.preset.preset_registry import PresetRegistry


class PresetManager:
    """
    Preset Layer Coordinator. Translates Preset selection (1-14) into Mode Request
    for MultiModeManager. DOES NOT publish /cmd_vel directly.
    """

    def __init__(self, mode_manager: Optional[MultiModeManager] = None):
        self.mode_manager = mode_manager
        self.registry = PresetRegistry()
        self._current_preset_id: int = 3  # Default to Preset 3 (MANUAL)
        self._lock = threading.Lock()

    def select_preset(self, preset_id: int, source: str = "PRESET_LAYER") -> Tuple[bool, str]:
        """Select preset number 1-14 and forward mode switch to ModeManager."""
        defn = self.registry.get_preset(preset_id)
        if not defn:
            return False, f"Invalid Preset ID: {preset_id} (Must be between 1 and 14)"

        with self._lock:
            self._current_preset_id = preset_id

        if self.mode_manager is not None:
            success, reason = self.mode_manager.switch_mode(defn.target_mode)
            if success:
                return True, f"Preset {preset_id} [{defn.name}] activated -> Mode [{defn.target_mode.name}]"
            else:
                return False, f"Preset {preset_id} failed: {reason}"

        return True, f"Preset {preset_id} [{defn.name}] mapped to [{defn.target_mode.name}]"

    def get_current_preset_id(self) -> int:
        with self._lock:
            return self._current_preset_id
