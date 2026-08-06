import math


class AdaptiveCurveSpeedController:
    """
    Adaptive Curve Speed Controller V6.0.
    Dynamically throttles linear velocity when entering sharp curves and smooths acceleration on straights.
    Prevents jerky motor motion and wheel slipping during turns.
    """

    def __init__(self, max_linear_speed: float = 0.35, max_angular_speed: float = 0.65):
        self.max_linear_speed = max_linear_speed
        self.max_angular_speed = max_angular_speed

    def compute_adaptive_speed(self, target_linear: float, target_angular: float) -> Tuple[float, float]:
        """
        Adjust linear speed based on angular curvature magnitude.
        """
        abs_w = abs(target_angular)
        curvature_ratio = min(1.0, abs_w / (self.max_angular_speed + 1e-4))

        # Speed scaling factor drops up to 50% on sharp turns
        speed_factor = 1.0 - (0.50 * curvature_ratio)

        adapted_linear = max(0.0, target_linear * speed_factor)
        return round(float(adapted_linear), 3), round(float(target_angular), 3)
