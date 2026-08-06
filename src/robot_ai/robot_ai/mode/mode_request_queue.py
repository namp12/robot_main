import queue
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from robot_ai.mode_manager.mode_types import RobotMode


@dataclass
class ModeRequest:
    """Represents an incoming request to switch operating modes."""
    target_mode: RobotMode
    source: str  # E.g. "WEB", "VOICE", "HOTKEY", "REST_API", "SCHEDULER"
    timestamp: float
    reason: str = ""
    payload: Optional[Dict[str, Any]] = None


class ModeRequestQueue:
    """
    Thread-safe Mode Request Queue handling multi-source switch requests
    sequentially with sub-100ms latency.
    """

    def __init__(self, maxsize: int = 50):
        self._queue = queue.Queue(maxsize=maxsize)

    def push_request(self, target_mode: RobotMode, source: str, reason: str = "", payload: dict = None) -> bool:
        """Push a new mode switch request to the queue."""
        req = ModeRequest(
            target_mode=target_mode,
            source=source,
            timestamp=time.time(),
            reason=reason,
            payload=payload
        )
        try:
            self._queue.put_nowait(req)
            return True
        except queue.Full:
            return False

    def pop_request(self, timeout: float = 0.05) -> Optional[ModeRequest]:
        """Pop next pending mode request with a default short timeout."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear(self):
        """Clear all pending requests in queue."""
        with self._queue.mutex:
            self._queue.queue.clear()
