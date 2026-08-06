import time
import psutil
import threading
from typing import Dict, Any, Optional


class FeatureMonitor:
    """Realtime resource monitor tracking CPU, RAM, and Thread count for the active feature."""

    def __init__(self):
        self._lock = threading.Lock()

    def get_feature_telemetry(self, active_feature_id: Optional[str], duration_sec: float) -> Dict[str, Any]:
        with self._lock:
            return {
                "active_feature_id": active_feature_id if active_feature_id else "NONE",
                "running_time_sec": round(duration_sec, 1),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "ram_percent": psutil.virtual_memory().percent,
                "thread_count": threading.active_count(),
                "timestamp": time.time()
            }
