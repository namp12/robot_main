import time
import math
from typing import Dict, Any, List, Optional, Tuple


class DynamicObstaclePredictor:
    """
    Dynamic Obstacle Trajectory Predictor V6.0.
    Forecasts positions of moving obstacles (people, carts, moving objects) up to 1.5m ahead
    by tracking displacement vectors over time.
    """

    def __init__(self, forecast_time_horizon_sec: float = 1.5):
        self.forecast_horizon = forecast_time_horizon_sec
        self._obstacle_history: Dict[str, List[Tuple[float, float, float]]] = {}  # id -> [(x, y, ts)]

    def update_obstacle_position(self, obstacle_id: str, x: float, y: float):
        now = time.time()
        if obstacle_id not in self._obstacle_history:
            self._obstacle_history[obstacle_id] = []
        self._obstacle_history[obstacle_id].append((x, y, now))

        # Keep history up to 2.0s
        self._obstacle_history[obstacle_id] = [
            pt for pt in self._obstacle_history[obstacle_id] if (now - pt[2]) <= 2.0
        ]

    def predict_future_position(self, obstacle_id: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Predict future position (pred_x, pred_y, vx, vy) at forecast_horizon.
        """
        pts = self._obstacle_history.get(obstacle_id, [])
        if len(pts) < 2:
            return None

        p_old = pts[0]
        p_new = pts[-1]
        dt = p_new[2] - p_old[2]
        if dt <= 0.05:
            return None

        vx = (p_new[0] - p_old[0]) / dt
        vy = (p_new[1] - p_old[1]) / dt

        pred_x = p_new[0] + (vx * self.forecast_horizon)
        pred_y = p_new[1] + (vy * self.forecast_horizon)

        return round(float(pred_x), 3), round(float(pred_y), 3), round(float(vx), 3), round(float(vy), 3)
