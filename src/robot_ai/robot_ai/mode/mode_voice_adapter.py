from typing import Optional, Tuple
from robot_ai.mode_manager.mode_types import RobotMode


class ModeVoiceAdapter:
    """
    Translates Vietnamese spoken voice commands into RobotMode switch intents.
    """

    def __init__(self):
        self._intent_rules = [
            # EMERGENCY STOP
            (["dừng khẩn", "khẩn cấp", "dừng lại ngay", "stop emergency"], RobotMode.EMERGENCY_STOP),
            # SAFE MANUAL
            (["lái an toàn", "phanh an toàn"], RobotMode.SAFE_MANUAL),
            # MANUAL
            (["chế độ lái tay", "lái tay", "điều khiển thủ công"], RobotMode.MANUAL),
            # GO TO GOAL
            (["đi tới mục tiêu", "đến điểm", "di chuyển tới"], RobotMode.GO_TO_GOAL),
            # FOLLOW PERSON
            (["bám theo tôi", "theo tôi", "đi theo tôi", "follow me"], RobotMode.FOLLOW_PERSON),
            # PATROL
            (["đi tuần tra", "tuần tra", "khảo sát"], RobotMode.PATROL),
            # DELIVERY
            (["giao hàng", "vận chuyển hàng"], RobotMode.DELIVERY),
            # RETURN HOME
            (["về nhà", "trở về nhà", "quay về trạm"], RobotMode.RETURN_HOME),
            # AUTO EXPLORE
            (["chế độ tự hành", "tự hành", "thăm dò tự động", "tự chạy"], RobotMode.AUTO_EXPLORE),
            # VOICE ASSISTANT
            (["trợ lý giọng nói", "nói chuyện", "trò chuyện"], RobotMode.VOICE_ASSISTANT),
            # DOCKING
            (["vào trạm sạc", "sạc pin"], RobotMode.DOCKING),
        ]

    def parse_voice_intent(self, text: str) -> Optional[Tuple[RobotMode, str]]:
        """Parse spoken text for mode switch intent."""
        clean_text = text.strip().lower()

        for keywords, mode in self._intent_rules:
            if any(k in clean_text for k in keywords):
                return mode, f"Voice Command Matched: '{clean_text}'"

        return None
