import time
import threading
from typing import Dict, Any
from robot_ai.preset.preset_registry import PRESET_DEFINITIONS


class PresetStatusTracker:
    """Tracks current preset selection status telemetry."""

    def __init__(self, initial_preset_id: int = 3):
        self._current_preset_id = initial_preset_id
        self._last_source = "SYSTEM"
        self._update_ts = time.time()
        self._lock = threading.Lock()

    def update_preset(self, preset_id: int, source: str = "SYSTEM"):
        with self._lock:
            self._current_preset_id = preset_id
            self._last_source = source
            self._update_ts = time.time()

    def get_status_dict(self) -> Dict[str, Any]:
        with self._lock:
            defn = PRESET_DEFINITIONS.get(self._current_preset_id)
            return {
                "preset_id": self._current_preset_id,
                "preset_name": defn.name if defn else "Unknown",
                "target_mode": defn.target_mode.name if defn else "UNKNOWN",
                "source": self._last_source,
                "timestamp": self._update_ts,
                "running_time_sec": round(time.time() - self._update_ts, 1)
            }
