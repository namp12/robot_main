from dataclasses import dataclass, field
from typing import Dict, List, Optional
from robot_ai.mode_manager.mode_types import RobotMode, MODE_PRIORITY


@dataclass
class ModeDefinition:
    """Metadata definition for a single robot operating mode."""
    mode: RobotMode
    name: str
    icon: str
    description: str
    priority: int
    hotkey: str
    voice_aliases: List[str] = field(default_factory=list)
    api_alias: str = ""
    color: str = "#3B82F6"
    category: str = "GENERAL"
    enabled: bool = True
    visible: bool = True


class ModeRegistry:
    """
    Central Mode Registry mapping all 14 supported modes to UI/Voice/API metadata.
    """

    def __init__(self):
        self._registry: Dict[RobotMode, ModeDefinition] = {}
        self._build_registry()

    def _build_registry(self):
        definitions = [
            ModeDefinition(
                mode=RobotMode.EMERGENCY_STOP,
                name="EMERGENCY_STOP",
                icon="🚨",
                description="Dừng khẩn cấp toàn bộ động cơ và khóa hệ thống",
                priority=MODE_PRIORITY[RobotMode.EMERGENCY_STOP],
                hotkey="ESC",
                voice_aliases=["dừng khẩn", "khẩn cấp", "stop", "emergency"],
                api_alias="EMERGENCY_STOP",
                color="#EF4444",
                category="SAFETY"
            ),
            ModeDefinition(
                mode=RobotMode.SAFE_MANUAL,
                name="SAFE_MANUAL",
                icon="🛡️",
                description="Lái tay kết hợp hệ thống phanh tự động né va chạm",
                priority=MODE_PRIORITY[RobotMode.SAFE_MANUAL],
                hotkey="F2",
                voice_aliases=["lái an toàn", "safe manual"],
                api_alias="SAFE_MANUAL",
                color="#F59E0B",
                category="MANUAL"
            ),
            ModeDefinition(
                mode=RobotMode.MANUAL,
                name="MANUAL",
                icon="🕹️",
                description="Lái tay trực tiếp từ Joystick Web / Bàn phím / Lệnh thoại",
                priority=MODE_PRIORITY[RobotMode.MANUAL],
                hotkey="F1",
                voice_aliases=["lái tay", "thủ công", "manual"],
                api_alias="MANUAL",
                color="#3B82F6",
                category="MANUAL"
            ),
            ModeDefinition(
                mode=RobotMode.GO_TO_GOAL,
                name="GO_TO_GOAL",
                icon="🎯",
                description="Di chuyển đến vị trí mục tiêu được chỉ định",
                priority=MODE_PRIORITY[RobotMode.GO_TO_GOAL],
                hotkey="F4",
                voice_aliases=["đi tới mục tiêu", "đến điểm", "go to goal"],
                api_alias="GO_TO_GOAL",
                color="#10B981",
                category="NAVIGATION"
            ),
            ModeDefinition(
                mode=RobotMode.FOLLOW_PERSON,
                name="FOLLOW_PERSON",
                icon="👤",
                description="Tự động bám theo người bằng Camera AI YOLO11s",
                priority=MODE_PRIORITY[RobotMode.FOLLOW_PERSON],
                hotkey="F5",
                voice_aliases=["bám theo tôi", "theo tôi", "follow person"],
                api_alias="FOLLOW_PERSON",
                color="#8B5CF6",
                category="VISION"
            ),
            ModeDefinition(
                mode=RobotMode.FOLLOW_TARGET,
                name="FOLLOW_TARGET",
                icon="🏷️",
                description="Bám theo ArUco Marker / QR Code / Target",
                priority=MODE_PRIORITY[RobotMode.FOLLOW_TARGET],
                hotkey="F6",
                voice_aliases=["bám thẻ", "bám target"],
                api_alias="FOLLOW_TARGET",
                color="#EC4899",
                category="VISION"
            ),
            ModeDefinition(
                mode=RobotMode.PATROL,
                name="PATROL",
                icon="🔄",
                description="Tuần tra tự động theo chuỗi tọa độ A -> B -> C -> A",
                priority=MODE_PRIORITY[RobotMode.PATROL],
                hotkey="F7",
                voice_aliases=["tuần tra", "đi tuần", "patrol"],
                api_alias="PATROL",
                color="#06B6D4",
                category="NAVIGATION"
            ),
            ModeDefinition(
                mode=RobotMode.DELIVERY,
                name="DELIVERY",
                icon="📦",
                description="Nhiệm vụ giao hàng từ Kho đến Khách hàng",
                priority=MODE_PRIORITY[RobotMode.DELIVERY],
                hotkey="F8",
                voice_aliases=["giao hàng", "vận chuyển", "delivery"],
                api_alias="DELIVERY",
                color="#F97316",
                category="MISSION"
            ),
            ModeDefinition(
                mode=RobotMode.RETURN_HOME,
                name="RETURN_HOME",
                icon="🏠",
                description="Tự động di chuyển quay về vị trí Home ban đầu",
                priority=MODE_PRIORITY[RobotMode.RETURN_HOME],
                hotkey="F9",
                voice_aliases=["trở về nhà", "về nhà", "return home"],
                api_alias="RETURN_HOME",
                color="#14B8A6",
                category="NAVIGATION"
            ),
            ModeDefinition(
                mode=RobotMode.AUTO_EXPLORE,
                name="AUTO_EXPLORE",
                icon="🤖",
                description="Tự hành V3 né vật cản 360 độ và tự tìm đường trống",
                priority=MODE_PRIORITY[RobotMode.AUTO_EXPLORE],
                hotkey="F3",
                voice_aliases=["chế độ tự hành", "tự hành", "thăm dò", "auto explore"],
                api_alias="AUTO_EXPLORE",
                color="#6366F1",
                category="AUTONOMY"
            ),
            ModeDefinition(
                mode=RobotMode.INSPECTION,
                name="INSPECTION",
                icon="🔍",
                description="Kiểm tra tốc độ chậm, bật Camera AI và ghi log tối đa",
                priority=MODE_PRIORITY[RobotMode.INSPECTION],
                hotkey="F11",
                voice_aliases=["kiểm tra", "inspection"],
                api_alias="INSPECTION",
                color="#64748B",
                category="SPECIAL"
            ),
            ModeDefinition(
                mode=RobotMode.VOICE_ASSISTANT,
                name="VOICE_ASSISTANT",
                icon="🗣️",
                description="Robot đứng yên trò chuyện AI (PhoWhisper STT + LLM + TTS)",
                priority=MODE_PRIORITY[RobotMode.VOICE_ASSISTANT],
                hotkey="F10",
                voice_aliases=["trợ lý giọng nói", "trò chuyện", "voice assistant"],
                api_alias="VOICE_ASSISTANT",
                color="#A855F7",
                category="AI"
            ),
            ModeDefinition(
                mode=RobotMode.DOCKING,
                name="DOCKING",
                icon="🔌",
                description="Tự động di chuyển vào trạm sạc và căn chỉnh",
                priority=MODE_PRIORITY[RobotMode.DOCKING],
                hotkey="F12",
                voice_aliases=["sạc pin", "vào trạm sạc", "docking"],
                api_alias="DOCKING",
                color="#EAB308",
                category="SPECIAL"
            ),
            ModeDefinition(
                mode=RobotMode.SIMULATION,
                name="SIMULATION",
                icon="💻",
                description="Chế độ chạy giả lập dry-run không xuất xung động cơ",
                priority=MODE_PRIORITY[RobotMode.SIMULATION],
                hotkey="Shift+F1",
                voice_aliases=["giả lập", "simulation"],
                api_alias="SIMULATION",
                color="#94A3B8",
                category="SPECIAL"
            )
        ]

        for d in definitions:
            self._registry[d.mode] = d

    def get_definition(self, mode: RobotMode) -> Optional[ModeDefinition]:
        return self._registry.get(mode)

    def get_all_definitions(self) -> List[ModeDefinition]:
        return list(self._registry.values())
