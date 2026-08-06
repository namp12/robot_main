from dataclasses import dataclass, field
from typing import Dict, List, Optional
from robot_ai.mode_manager.mode_types import RobotMode


@dataclass
class PresetDefinition:
    preset_id: int
    name: str
    target_mode: RobotMode
    icon: str
    hotkey: str
    voice_aliases: List[str] = field(default_factory=list)


PRESET_DEFINITIONS: Dict[int, PresetDefinition] = {
    1: PresetDefinition(1, "Bám theo người", RobotMode.FOLLOW_PERSON, "👤", "Ctrl+1", ["chế độ một", "chế độ 1", "chế độ bám người"]),
    2: PresetDefinition(2, "Tự hành", RobotMode.AUTO_EXPLORE, "🤖", "Ctrl+2", ["chế độ hai", "chế độ 2", "chế độ tự hành"]),
    3: PresetDefinition(3, "Lái tay", RobotMode.MANUAL, "🕹️", "Ctrl+3", ["chế độ ba", "chế độ 3", "chế độ lái tay"]),
    4: PresetDefinition(4, "Lái tay an toàn", RobotMode.SAFE_MANUAL, "🛡️", "Ctrl+4", ["chế độ bốn", "chế độ 4", "lái an toàn"]),
    5: PresetDefinition(5, "Đi tới điểm", RobotMode.GO_TO_GOAL, "🎯", "Ctrl+5", ["chế độ năm", "chế độ 5", "tới mục tiêu"]),
    6: PresetDefinition(6, "Tuần tra", RobotMode.PATROL, "🔄", "Ctrl+6", ["chế độ sáu", "chế độ 6", "chế độ tuần tra"]),
    7: PresetDefinition(7, "Giao hàng", RobotMode.DELIVERY, "📦", "Ctrl+7", ["chế độ bảy", "chế độ 7", "chế độ giao hàng"]),
    8: PresetDefinition(8, "Về nhà", RobotMode.RETURN_HOME, "🏠", "Ctrl+8", ["chế độ tám", "chế độ 8", "về nhà"]),
    9: PresetDefinition(9, "Kiểm tra", RobotMode.INSPECTION, "🔍", "Ctrl+9", ["chế độ chín", "chế độ 9", "chế độ kiểm tra"]),
    10: PresetDefinition(10, "Trợ lý AI", RobotMode.VOICE_ASSISTANT, "🗣️", "Ctrl+0", ["chế độ mười", "chế độ 10", "trợ lý ai"]),
    11: PresetDefinition(11, "Bám mục tiêu", RobotMode.FOLLOW_TARGET, "🏷️", "Alt+1", ["chế độ mười một", "chế độ 11"]),
    12: PresetDefinition(12, "Sạc", RobotMode.DOCKING, "🔌", "Alt+2", ["chế độ mười hai", "chế độ 12", "vào trạm sạc"]),
    13: PresetDefinition(13, "Giả lập", RobotMode.SIMULATION, "💻", "Alt+3", ["chế độ mười ba", "chế độ 13"]),
    14: PresetDefinition(14, "Dừng khẩn", RobotMode.EMERGENCY_STOP, "🚨", "ESC", ["chế độ mười bốn", "chế độ 14", "dừng khẩn cấp"]),
}


class PresetRegistry:
    """Central Preset Registry accessing Preset 1-14 definitions."""
    def get_preset(self, preset_id: int) -> Optional[PresetDefinition]:
        return PRESET_DEFINITIONS.get(preset_id)

    def get_all_presets(self) -> List[PresetDefinition]:
        return list(PRESET_DEFINITIONS.values())
