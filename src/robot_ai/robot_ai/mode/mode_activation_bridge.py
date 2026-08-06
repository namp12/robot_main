import logging
from typing import Optional, Dict, Any

from robot_ai.feature.feature_manager import FeatureManager
from robot_ai.feature.feature_implementations import create_all_default_features
from robot_ai.mode.mode_sensor_profile import get_sensor_profile, ModeProfileConfig
from robot_ai.mode_manager.mode_types import RobotMode, API_ALIAS_TO_MODE

logger = logging.getLogger("ModeActivationBridge")


class ModeActivationBridge:
    """
    Bridge connecting Multi-Mode Control Framework V3.5, Quick Preset V1,
    and Exclusive Feature Framework V1.
    Guarantees clicking a Mode/Preset ACTUALLY triggers Feature teardown & activation.
    """

    def __init__(self, feature_manager: Optional[FeatureManager] = None):
        self.feature_manager = feature_manager or FeatureManager()
        self._register_default_features()
        self._current_mode: RobotMode = RobotMode.MANUAL

    def _register_default_features(self):
        features = create_all_default_features()
        for fid, impl in features.items():
            self.feature_manager.register_feature_implementation(fid, impl)

    def activate_mode(self, mode_input: Any, source: str = "MODE_ACTIVATION_BRIDGE") -> bool:
        """
        Activates a new Mode by executing full Feature Teardown -> Feature Activation pipeline.
        """
        target_mode: Optional[RobotMode] = None

        if isinstance(mode_input, RobotMode):
            target_mode = mode_input
        elif isinstance(mode_input, str):
            clean_str = mode_input.strip().upper().replace("MODE_", "")
            target_mode = API_ALIAS_TO_MODE.get(clean_str)

        if not target_mode:
            logger.warning(f"⚠️ [MODE_BRIDGE] Invalid mode input: {mode_input}")
            return False

        feature_id = target_mode.name
        ok, msg = self.feature_manager.switch_feature(feature_id, source=source)
        if ok:
            self._current_mode = target_mode
            logger.info(f"🟢 [MODE_BRIDGE] Mode '{target_mode.name}' successfully activated via Feature Framework.")
            return True
        else:
            logger.error(f"❌ [MODE_BRIDGE] Failed to activate Mode '{target_mode.name}': {msg}")
            return False

    def get_current_profile(self) -> ModeProfileConfig:
        return get_sensor_profile(self._current_mode)

    def get_active_telemetry_snapshot(self) -> Dict[str, Any]:
        profile = self.get_current_profile()
        return {
            "current_mode": profile.mode_name,
            "running_feature": profile.mode_name,
            "running_modules": profile.active_modules,
            "disabled_modules": profile.disabled_modules,
            "sensor_profile": {
                "camera_enabled": profile.camera_enabled,
                "yolo_enabled": profile.yolo_enabled,
                "lidar_enabled": profile.lidar_enabled,
                "planner_enabled": profile.planner_enabled,
            }
        }


# Global singleton instance
mode_activation_bridge = ModeActivationBridge()
