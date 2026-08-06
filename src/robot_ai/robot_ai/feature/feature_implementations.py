import logging
from typing import Dict, Any
from robot_ai.feature.feature_base import FeatureBase
from robot_ai.mode_manager.mode_types import RobotMode
from robot_ai.mode.mode_sensor_profile import get_sensor_profile, ModeProfileConfig

logger = logging.getLogger("FeatureImplementations")


class StandardModeFeature(FeatureBase):
    """
    Standard Feature implementation wrapping RobotMode.
    Enforces clean isolation of modules, sensors, timers, and callbacks per mode.
    """

    def __init__(self, feature_id: str, mode: RobotMode):
        super().__init__(feature_id)
        self.mode = mode
        self.profile: ModeProfileConfig = get_sensor_profile(mode)

    def on_initialize(self) -> bool:
        logger.info(f"⚙️ [INIT] Initialized Feature '{self.name}' (Mode: {self.mode.name})")
        return True

    def on_start(self) -> bool:
        logger.info(f"🟢 [START] Activated Feature '{self.name}' (Mode: {self.mode.name})")
        logger.info(f"   Active Modules: {self.profile.active_modules}")
        logger.info(f"   Disabled Modules: {self.profile.disabled_modules}")
        return True

    def on_pause(self) -> bool:
        logger.info(f"⏸️ [PAUSE] Paused Feature '{self.name}'")
        return True

    def on_resume(self) -> bool:
        logger.info(f"▶️ [RESUME] Resumed Feature '{self.name}'")
        return True

    def on_stop(self) -> bool:
        logger.info(f"🔴 [STOP] Stopped Feature '{self.name}'")
        return True

    def on_cleanup(self) -> bool:
        logger.info(f"🧹 [CLEANUP] Cleaned up Feature '{self.name}' background tasks")
        return True

    def on_release(self) -> bool:
        logger.info(f"🔓 [RELEASE] Released Feature '{self.name}' resources")
        return True


from robot_ai.feature.feature_v2_implementations import FollowPersonFeature, AutoExploreFeature


def create_all_default_features() -> Dict[str, FeatureBase]:
    """Factory creating feature implementation instances for all 14 modes."""
    default_features: Dict[str, FeatureBase] = {
        "MANUAL": StandardModeFeature("MANUAL", RobotMode.MANUAL),
        "SAFE_MANUAL": StandardModeFeature("SAFE_MANUAL", RobotMode.SAFE_MANUAL),
        "FOLLOW_PERSON": FollowPersonFeature(),
        "FOLLOW_TARGET": StandardModeFeature("FOLLOW_TARGET", RobotMode.FOLLOW_TARGET),
        "AUTO_EXPLORE": AutoExploreFeature(),
        "GO_TO_GOAL": StandardModeFeature("GO_TO_GOAL", RobotMode.GO_TO_GOAL),
        "PATROL": StandardModeFeature("PATROL", RobotMode.PATROL),
        "DELIVERY": StandardModeFeature("DELIVERY", RobotMode.DELIVERY),
        "RETURN_HOME": StandardModeFeature("RETURN_HOME", RobotMode.RETURN_HOME),
        "INSPECTION": StandardModeFeature("INSPECTION", RobotMode.INSPECTION),
        "VOICE_ASSISTANT": StandardModeFeature("VOICE_ASSISTANT", RobotMode.VOICE_ASSISTANT),
        "DOCKING": StandardModeFeature("DOCKING", RobotMode.DOCKING),
        "SIMULATION": StandardModeFeature("SIMULATION", RobotMode.SIMULATION),
        "EMERGENCY_STOP": StandardModeFeature("EMERGENCY_STOP", RobotMode.EMERGENCY_STOP),
    }
    return default_features
