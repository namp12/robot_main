import threading
from typing import Callable, List, Dict, Any
from robot_ai.mode_manager.mode_events import ModeEventType


class ModeEventBus:
    """
    Decoupled Event Bus for mode orchestration lifecycle events.
    """

    def __init__(self):
        self._subscribers: Dict[ModeEventType, List[Callable[[Dict[str, Any]], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: ModeEventType, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to a specific ModeEventType."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def publish(self, event_type: ModeEventType, data: Dict[str, Any]):
        """Publish event to all registered subscribers."""
        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))

        for cb in callbacks:
            try:
                cb(data)
            except Exception:
                pass
