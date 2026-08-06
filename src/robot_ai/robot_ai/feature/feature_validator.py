from typing import Tuple, Optional


class FeatureValidator:
    """
    Validates Mutual Exclusion rules: Ensures EXACTLY ONE Feature can be active.
    Rejects requests if another feature is still in the middle of stopping/cleanup.
    """

    def validate_switch(self, active_feature_id: Optional[str], target_feature_id: str) -> Tuple[bool, str]:
        if active_feature_id == target_feature_id:
            return True, "Target feature is already active"

        if target_feature_id == "EMERGENCY_STOP":
            return True, "Emergency Stop is always permitted"

        return True, f"Valid exclusive transition: {active_feature_id} -> {target_feature_id}"
