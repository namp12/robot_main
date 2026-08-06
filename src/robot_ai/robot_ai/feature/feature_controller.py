from typing import Tuple, Optional
from robot_ai.feature.feature_manager import FeatureManager
from robot_ai.feature.feature_monitor import FeatureMonitor


class FeatureController:
    """
    High-level Feature Controller orchestrating request -> stop -> cleanup -> release -> start pipeline.
    """

    def __init__(self, manager: FeatureManager):
        self.manager = manager
        self.monitor = FeatureMonitor()

    def request_feature_switch(self, feature_id: str, source: str = "CONTROLLER") -> Tuple[bool, str]:
        """Request exclusive feature switch."""
        return self.manager.switch_feature(feature_id, source=source)

    def get_telemetry(self) -> dict:
        """Return live telemetry snapshot."""
        active_id = self.manager.get_active_feature_id()
        dur = self.manager.get_active_feature_duration()
        return self.monitor.get_feature_telemetry(active_id, dur)
