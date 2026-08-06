import time
import threading
from typing import Dict, Optional, Tuple

from robot_ai.feature.feature_base import FeatureBase
from robot_ai.feature.feature_registry import FeatureRegistry
from robot_ai.feature.feature_validator import FeatureValidator
from robot_ai.feature.feature_resource_manager import FeatureResourceManager
from robot_ai.feature.feature_event_bus import FeatureEventBus, FeatureEventType
from robot_ai.feature.feature_history import FeatureHistoryRecorder
from robot_ai.feature.feature_logger import FeatureLogger


class FeatureManager:
    """
    Core Exclusive Feature Manager.
    Enforces EXACTLY ONE ACTIVE FEATURE running at any given moment.
    Executes mandatory Stop -> Cleanup -> Release -> Stopped pipeline before starting next feature.
    """

    def __init__(self):
        self.registry = FeatureRegistry()
        self.validator = FeatureValidator()
        self.resource_manager = FeatureResourceManager()
        self.event_bus = FeatureEventBus()
        self.history = FeatureHistoryRecorder()
        self.logger = FeatureLogger()

        self._registered_features: Dict[str, FeatureBase] = {}
        self._active_feature_id: Optional[str] = None
        self._active_feature_start_ts: float = 0.0

        self._lock = threading.Lock()

    def register_feature_implementation(self, feature_id: str, impl: FeatureBase):
        """Register a feature implementation instance."""
        with self._lock:
            self._registered_features[feature_id.upper()] = impl

    def switch_feature(self, target_feature_id: str, source: str = "SYSTEM") -> Tuple[bool, str]:
        """
        Switch to a new exclusive feature.
        Guarantees previous active feature is 100% Stopped, Cleaned up, and Released
        BEFORE target feature starts.
        """
        target_id = target_feature_id.upper()
        defn = self.registry.get_feature(target_id)
        if not defn:
            return False, f"Unknown Feature ID: '{target_feature_id}'"

        with self._lock:
            current_id = self._active_feature_id

            # 1. Check if same feature already active
            if current_id == target_id:
                return True, f"Feature '{target_id}' is already active"

            # 2. Validate switch
            valid, reason = self.validator.validate_switch(current_id, target_id)
            if not valid:
                return False, reason

            # 3. STOP, CLEANUP & RELEASE current active feature
            if current_id and current_id in self._registered_features:
                old_impl = self._registered_features[current_id]
                duration = time.time() - self._active_feature_start_ts

                self.event_bus.publish(FeatureEventType.FEATURE_STOPPING, {"feature_id": current_id})
                self.logger.log_stop(current_id, duration)

                # Stop execution
                old_impl.stop()

                # Release tracked background resources
                self.resource_manager.release_feature_resources(current_id)
                self.logger.log_cleanup(current_id)
                self.logger.log_release(current_id)

                self.event_bus.publish(FeatureEventType.FEATURE_STOPPED, {"feature_id": current_id})
                self.history.record_event(current_id, "STOP", source=source, duration_sec=duration)

            self._active_feature_id = None

            # 4. START next feature
            if target_id in self._registered_features:
                new_impl = self._registered_features[target_id]

                self.event_bus.publish(FeatureEventType.FEATURE_STARTING, {"feature_id": target_id})
                self.logger.log_start(target_id, source)

                start_ok = new_impl.start()
                if not start_ok:
                    self.event_bus.publish(FeatureEventType.FEATURE_FAILED, {"feature_id": target_id})
                    return False, f"Failed to start Feature '{target_id}'"

            self._active_feature_id = target_id
            self._active_feature_start_ts = time.time()
            self.event_bus.publish(FeatureEventType.FEATURE_STARTED, {"feature_id": target_id})
            self.history.record_event(target_id, "START", source=source)

        return True, f"Successfully switched exclusive feature: '{current_id}' -> '{target_id}'"

    def get_active_feature_id(self) -> Optional[str]:
        with self._lock:
            return self._active_feature_id

    def get_active_feature_duration(self) -> float:
        with self._lock:
            if self._active_feature_id:
                return round(time.time() - self._active_feature_start_ts, 1)
            return 0.0
