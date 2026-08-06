from enum import Enum, auto
import time
import threading
from typing import Tuple


class FeatureState(Enum):
    REGISTERED = auto()
    INITIALIZED = auto()
    READY = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSING = auto()
    PAUSED = auto()
    RESUMING = auto()
    STOPPING = auto()
    STOPPED = auto()
    CLEANUP = auto()
    RELEASED = auto()
    FAILED = auto()


class FeatureStateMachine:
    """Tracks state transitions for a single feature lifecycle."""

    def __init__(self, feature_id: str):
        self.feature_id = feature_id
        self._state = FeatureState.REGISTERED
        self._last_transition_ts = time.time()
        self._lock = threading.Lock()

    def get_state(self) -> FeatureState:
        with self._lock:
            return self._state

    def transition_to(self, target_state: FeatureState) -> Tuple[bool, str]:
        with self._lock:
            prev = self._state
            self._state = target_state
            self._last_transition_ts = time.time()
            return True, f"{self.feature_id} transitioned: {prev.name} -> {target_state.name}"
