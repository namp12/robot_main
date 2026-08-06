from typing import Optional, Tuple
from robot_ai.preset.preset_registry import PRESET_DEFINITIONS


class PresetHotkeyAdapter:
    """Translates keyboard hotkeys to Preset IDs."""

    def parse_preset_hotkey(self, key_combination: str) -> Optional[Tuple[int, str]]:
        clean_key = key_combination.strip()

        for pid, defn in PRESET_DEFINITIONS.items():
            if defn.hotkey.lower() == clean_key.lower():
                return pid, f"Hotkey Preset Shortcut: [{defn.hotkey}] -> Preset {pid}"

        return None
