from enum import Enum, auto
import time
import json
import threading
from typing import Callable, List, Dict, Any


class ModeEventType(Enum):
    MODE_CHANGED = auto()
    MODE_STARTED = auto()
    MODE_STOPPED = auto()
    MODE_PAUSED = auto()
    MODE_RESUMED = auto()
    GOAL_REACHED = auto()
    FOLLOW_LOST = auto()
    OBSTACLE_DETECTED = auto()
    RECOVERY_STARTED = auto()
    RECOVERY_FINISHED = auto()
    EMERGENCY_TRIGGERED = auto()
    EMERGENCY_CLEARED = auto()


class ModeEventEngine:
    """
    Decoupled Event System broadcasting mode lifecycle and state events.
    """

    def __init__(self):
        self._listeners: List[Callable[[ModeEventType, Dict[str, Any]], None]] = []
        self._lock = threading.Lock()

    def register_listener(self, listener: Callable[[ModeEventType, Dict[str, Any]], None]):
        """Register event listener callback."""
        with self._lock:
            self._listeners.append(listener)

    def dispatch_event(self, event_type: ModeEventType, data: Dict[str, Any] = None):
        """Dispatch event asynchronously to all registered listeners."""
        if data is None:
            data = {}
        data["timestamp"] = time.time()
        data["event"] = event_type.name

        with self._lock:
            listeners_copy = list(self._listeners)

        for callback in listeners_copy:
            try:
                callback(event_type, data)
            except Exception:
                pass
