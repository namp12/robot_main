import threading
from typing import List, Callable, Dict


class FeatureResourceManager:
    """
    Tracks and releases background timers, worker threads, and callbacks
    belonging to an active feature when it transitions to STOPPED.
    """

    def __init__(self):
        self._registered_cleanups: Dict[str, List[Callable[[], None]]] = {}
        self._lock = threading.Lock()

    def register_cleanup_action(self, feature_id: str, action: Callable[[], None]):
        with self._lock:
            if feature_id not in self._registered_cleanups:
                self._registered_cleanups[feature_id] = []
            self._registered_cleanups[feature_id].append(action)

    def release_feature_resources(self, feature_id: str):
        with self._lock:
            actions = self._registered_cleanups.pop(feature_id, [])

        for act in actions:
            try:
                act()
            except Exception:
                pass
