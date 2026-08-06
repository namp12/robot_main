import logging
from enum import Enum, auto
from typing import Dict, Any, Tuple

logger = logging.getLogger("AutonomousDecisionMaker")


class DecisionState(Enum):
    EMERGENCY_STOP = auto()
    ASSISTANCE_NEEDED = auto()
    YIELD_AND_SLOWDOWN = auto()
    CORRIDOR_GLIDE = auto()


class AutonomousDecisionMaker:
    """
    Multi-Sensor Autonomous Decision Engine V5.0.
    Evaluates fused 5-sensor snapshot to decide navigation state and velocity multipliers.
    """

    def decide_navigation_action(self, perception: Dict[str, Any]) -> Tuple[DecisionState, float, str]:
        """
        Returns (DecisionState, SpeedMultiplier, ActionReason).
        """
        fused_front_m = perception.get("fused_front_distance_meters", 99.0)
        tilt_hazard = perception.get("tilt_hazard", False)
        detections = perception.get("ai_detections", [])

        # 1. EMERGENCY STOP GUARD
        if tilt_hazard:
            return DecisionState.EMERGENCY_STOP, 0.0, "EMERGENCY_TILT_HAZARD_EXCEEDED"
        if fused_front_m <= 0.15:
            return DecisionState.EMERGENCY_STOP, 0.0, "EMERGENCY_OBSTACLE_TOO_CLOSE"

        # 2. ASSISTANCE NEEDED GUARD (Door / Elevator)
        for det in detections:
            label = det.get("label", "").lower()
            if any(kw in label for kw in ["door", "elevator", "gate", "cửa", "thang máy"]) and fused_front_m < 0.8:
                return DecisionState.ASSISTANCE_NEEDED, 0.0, f"BARRIER_DETECTED_{label.upper()}"

        # 3. YIELD AND SLOWDOWN GUARD (Movable Obstacles: Person, Chair, Table, Trash Can)
        if 0.15 < fused_front_m <= 0.8:
            return DecisionState.YIELD_AND_SLOWDOWN, 0.40, "OBSTACLE_SLOWDOWN_60_PERCENT"

        # 4. FREE SPACE CORRIDOR GLIDE
        return DecisionState.CORRIDOR_GLIDE, 1.0, "FREE_SPACE_CORRIDOR_GLIDE"
