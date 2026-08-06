import time
import threading
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PresetHistoryEntry:
    timestamp: float
    preset_id: int
    preset_name: str
    target_mode: str
    source: str
    reason: str


class PresetHistoryRecorder:
    """Stores up to max_capacity recent preset selection records."""

    def __init__(self, max_capacity: int = 100):
        self.max_capacity = max_capacity
        self._history: List[PresetHistoryEntry] = []
        self._lock = threading.Lock()

    def record_preset(self, preset_id: int, preset_name: str, target_mode: str, source: str, reason: str):
        entry = PresetHistoryEntry(
            timestamp=time.time(),
            preset_id=preset_id,
            preset_name=preset_name,
            target_mode=target_mode,
            source=source,
            reason=reason
        )
        with self._lock:
            self._history.append(entry)
            if len(self._history) > self.max_capacity:
                self._history.pop(0)

    def get_recent_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            recent = self._history[-limit:]
            return [
                {
                    "timestamp": e.timestamp,
                    "preset_id": e.preset_id,
                    "preset_name": e.preset_name,
                    "target_mode": e.target_mode,
                    "source": e.source,
                    "reason": e.reason
                }
                for e in reversed(recent)
            ]
