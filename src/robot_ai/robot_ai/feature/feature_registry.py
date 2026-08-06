from dataclasses import dataclass, field
from typing import Dict, List, Optional
from robot_ai.mode_manager.mode_types import RobotMode, MODE_PRIORITY


@dataclass
class FeatureDefinition:
    feature_id: str
    display_name: str
    target_mode: RobotMode
    category: str
    priority: int
    resource_profile: str = "DEFAULT"
    enabled: bool = True


FEATURE_DEFINITIONS: Dict[str, FeatureDefinition] = {
    "EMERGENCY_STOP": FeatureDefinition("EMERGENCY_STOP", "Dừng khẩn cấp", RobotMode.EMERGENCY_STOP, "SAFETY", MODE_PRIORITY[RobotMode.EMERGENCY_STOP]),
    "SAFE_MANUAL": FeatureDefinition("SAFE_MANUAL", "Lái tay an toàn", RobotMode.SAFE_MANUAL, "MANUAL", MODE_PRIORITY[RobotMode.SAFE_MANUAL]),
    "MANUAL": FeatureDefinition("MANUAL", "Lái tay thủ công", RobotMode.MANUAL, "MANUAL", MODE_PRIORITY[RobotMode.MANUAL]),
    "GO_TO_GOAL": FeatureDefinition("GO_TO_GOAL", "Đi tới mục tiêu", RobotMode.GO_TO_GOAL, "NAVIGATION", MODE_PRIORITY[RobotMode.GO_TO_GOAL]),
    "FOLLOW_PERSON": FeatureDefinition("FOLLOW_PERSON", "Bám theo người", RobotMode.FOLLOW_PERSON, "VISION", MODE_PRIORITY[RobotMode.FOLLOW_PERSON]),
    "FOLLOW_TARGET": FeatureDefinition("FOLLOW_TARGET", "Bám mục tiêu", RobotMode.FOLLOW_TARGET, "VISION", MODE_PRIORITY[RobotMode.FOLLOW_TARGET]),
    "PATROL": FeatureDefinition("PATROL", "Tuần tra tự động", RobotMode.PATROL, "NAVIGATION", MODE_PRIORITY[RobotMode.PATROL]),
    "DELIVERY": FeatureDefinition("DELIVERY", "Giao hàng thông minh", RobotMode.DELIVERY, "MISSION", MODE_PRIORITY[RobotMode.DELIVERY]),
    "RETURN_HOME": FeatureDefinition("RETURN_HOME", "Về nhà", RobotMode.RETURN_HOME, "NAVIGATION", MODE_PRIORITY[RobotMode.RETURN_HOME]),
    "AUTO_EXPLORE": FeatureDefinition("AUTO_EXPLORE", "Tự hành né vật cản 360", RobotMode.AUTO_EXPLORE, "AUTONOMY", MODE_PRIORITY[RobotMode.AUTO_EXPLORE]),
    "INSPECTION": FeatureDefinition("INSPECTION", "Giám sát / Kiểm tra", RobotMode.INSPECTION, "SPECIAL", MODE_PRIORITY[RobotMode.INSPECTION]),
    "VOICE_ASSISTANT": FeatureDefinition("VOICE_ASSISTANT", "Trợ lý giọng nói", RobotMode.VOICE_ASSISTANT, "AI", MODE_PRIORITY[RobotMode.VOICE_ASSISTANT]),
    "DOCKING": FeatureDefinition("DOCKING", "Vào trạm sạc", RobotMode.DOCKING, "SPECIAL", MODE_PRIORITY[RobotMode.DOCKING]),
    "SIMULATION": FeatureDefinition("SIMULATION", "Giả lập dry-run", RobotMode.SIMULATION, "SPECIAL", MODE_PRIORITY[RobotMode.SIMULATION]),
}


class FeatureRegistry:
    """Central Feature Registry for the 14 exclusive features."""
    def get_feature(self, feature_id: str) -> Optional[FeatureDefinition]:
        return FEATURE_DEFINITIONS.get(feature_id.upper())

    def get_all_features(self) -> List[FeatureDefinition]:
        return list(FEATURE_DEFINITIONS.values())
