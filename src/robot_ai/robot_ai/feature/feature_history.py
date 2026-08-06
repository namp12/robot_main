import time
import threading
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class FeatureHistoryRecord:
    timestamp: float
    feature_id: str
    action: str  # E.g., START, STOP, CLEANUP, RELEASE
    source: str
    duration_sec: float
    success: bool


class FeatureHistoryRecorder:
    """Stores up to max_capacity (1000) recent feature execution records."""

    def __init__(self, max_capacity: int = 1000):
        self.max_capacity = max_capacity
        self._history: List[FeatureHistoryRecord] = []
        self._lock = threading.Lock()

    def record_event(self, feature_id: str, action: str, source: str = "SYSTEM", duration_sec: float = 0.0, success: bool = True):
        rec = FeatureHistoryRecord(
            timestamp=time.time(),
            feature_id=feature_id,
            action=action,
            source=source,
            duration_sec=duration_sec,
            success=success
        )
        with self._lock:
            self._history.append(rec)
            if len(self._history) > self.max_capacity:
                self._history.pop(0)

    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            recent = self._history[-limit:]
            return [
                {
                    "timestamp": r.timestamp,
                    "feature_id": r.feature_id,
                    "action": r.action,
                    "source": r.source,
                    "duration_sec": r.duration_sec,
                    "success": r.success
                }
                for r in reversed(recent)
            ]
