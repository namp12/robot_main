from enum import Enum, auto
import time
import threading
from typing import Callable, List, Dict, Any


class FeatureEventType(Enum):
    FEATURE_REQUESTED = auto()
    FEATURE_STARTING = auto()
    FEATURE_STARTED = auto()
    FEATURE_PAUSED = auto()
    FEATURE_RESUMED = auto()
    FEATURE_STOPPING = auto()
    FEATURE_STOPPED = auto()
    FEATURE_CLEANUP = auto()
    FEATURE_RELEASED = auto()
    FEATURE_FAILED = auto()


class FeatureEventBus:
    """Decoupled Event Bus for feature lifecycle events."""

    def __init__(self):
        self._subscribers: Dict[FeatureEventType, List[Callable[[Dict[str, Any]], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: FeatureEventType, callback: Callable[[Dict[str, Any]], None]):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def publish(self, event_type: FeatureEventType, data: Dict[str, Any]):
        if data is None:
            data = {}
        data["event"] = event_type.name
        data["timestamp"] = time.time()

        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))

        for cb in callbacks:
            try:
                cb(data)
            except Exception:
                pass
