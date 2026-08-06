from typing import Optional, Tuple


class PresetApiAdapter:
    """Translates REST API body payload to Preset ID."""

    def parse_api_preset(self, preset_value: int) -> Optional[Tuple[int, str]]:
        if 1 <= preset_value <= 14:
            return preset_value, f"REST API Call: Preset {preset_value}"
        return None
