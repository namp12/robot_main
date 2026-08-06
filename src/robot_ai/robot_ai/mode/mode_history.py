import time
import threading
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ModeHistoryEntry:
    timestamp: float
    from_mode: str
    to_mode: str
    source: str
    reason: str
    success: bool


class ModeHistoryRecorder:
    """
    Stores up to max_capacity recent mode transition records for debugging & audit logs.
    """

    def __init__(self, max_capacity: int = 100):
        self.max_capacity = max_capacity
        self._history: List[ModeHistoryEntry] = []
        self._lock = threading.Lock()

    def record_transition(self, from_mode: str, to_mode: str, source: str, reason: str, success: bool = True):
        entry = ModeHistoryEntry(
            timestamp=time.time(),
            from_mode=from_mode,
            to_mode=to_mode,
            source=source,
            reason=reason,
            success=success
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
                    "from_mode": e.from_mode,
                    "to_mode": e.to_mode,
                    "source": e.source,
                    "reason": e.reason,
                    "success": e.success
                }
                for e in reversed(recent)
            ]
