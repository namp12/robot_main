from typing import Optional, Tuple
from robot_ai.preset.preset_registry import PRESET_DEFINITIONS


class PresetVoiceAdapter:
    """Translates spoken Vietnamese preset phrases to Preset IDs."""

    def parse_preset_voice(self, text: str) -> Optional[Tuple[int, str]]:
        clean_text = text.strip().lower()

        for pid, defn in PRESET_DEFINITIONS.items():
            if any(alias in clean_text for alias in defn.voice_aliases):
                return pid, f"Voice Preset Matched: Preset {pid} [{defn.name}]"

        return None
