from typing import Optional, Tuple


class PresetWebAdapter:
    """Translates Web Dashboard Preset selection click to Preset ID."""

    def parse_web_preset(self, preset_val: str) -> Optional[Tuple[int, str]]:
        try:
            pid = int(preset_val)
            if 1 <= pid <= 14:
                return pid, f"Web Panel 1-Click Preset {pid}"
        except ValueError:
            pass
        return None
