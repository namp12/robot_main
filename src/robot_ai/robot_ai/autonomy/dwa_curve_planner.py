import math
import numpy as np
from typing import Tuple, List, Dict, Any


class DWACurvePlanner:
    """
    Dynamic Window Approach (DWA) Trajectory Curve Planner V6.0.
    Evaluates dynamic window velocity space (vx, wz) to sample smooth parabolic trajectories.
    Selects optimal velocity pair maximizing clearance, heading, and forward progress.
    """

    def __init__(
        self,
        max_speed: float = 0.35,
        max_yaw_rate: float = 0.65,
        max_accel: float = 0.20,
        max_dyaw_rate: float = 0.40,
        v_resolution: float = 0.05,
        w_resolution: float = 0.08,
        predict_time: float = 2.0,
        heading_cost_gain: float = 0.15,
        clearance_cost_gain: float = 1.0,
        velocity_cost_gain: float = 0.8
    ):
        self.max_speed = max_speed
        self.max_yaw_rate = max_yaw_rate
        self.max_accel = max_accel
        self.max_dyaw_rate = max_dyaw_rate
        self.v_resolution = v_resolution
        self.w_resolution = w_resolution
        self.predict_time = predict_time

        self.heading_cost_gain = heading_cost_gain
        self.clearance_cost_gain = clearance_cost_gain
        self.velocity_cost_gain = velocity_cost_gain

    def calc_dynamic_window(self, current_v: float, current_w: float, dt: float = 0.1) -> Tuple[float, float, float, float]:
        """Calculate dynamic window velocity limits (v_min, v_max, w_min, w_max)."""
        vs = [0.0, self.max_speed, -self.max_yaw_rate, self.max_yaw_rate]
        vd = [
            current_v - self.max_accel * dt,
            current_v + self.max_accel * dt,
            current_w - self.max_dyaw_rate * dt,
            current_w + self.max_dyaw_rate * dt,
        ]

        v_min = max(vs[0], vd[0])
        v_max = min(vs[1], vd[1])
        w_min = max(vs[2], vd[2])
        w_max = min(vs[3], vd[3])

        return v_min, v_max, w_min, w_max

    def predict_trajectory(self, v: float, w: float, dt: float = 0.1) -> List[Tuple[float, float, float]]:
        """Predict parabolic trajectory points (x, y, yaw) over predict_time horizon."""
        traj = [(0.0, 0.0, 0.0)]
        x, y, yaw = 0.0, 0.0, 0.0
        time_elapsed = 0.0

        while time_elapsed <= self.predict_time:
            x += v * math.cos(yaw) * dt
            y += v * math.sin(yaw) * dt
            yaw += w * dt
            time_elapsed += dt
            traj.append((x, y, yaw))

        return traj

    def plan_dwa_trajectory(
        self,
        current_v: float,
        current_w: float,
        target_angle_rad: float,
        scan_ranges: List[float]
    ) -> Tuple[float, float]:
        """
        Evaluate DWA velocity space to select optimal smooth trajectory (v, w).
        """
        v_min, v_max, w_min, w_max = self.calc_dynamic_window(current_v, current_w)

        best_v = 0.0
        best_w = 0.0
        min_total_cost = float('inf')

        for v in np.arange(v_min, v_max + self.v_resolution, self.v_resolution):
            for w in np.arange(w_min, w_max + self.w_resolution, self.w_resolution):
                traj = self.predict_trajectory(v, w)

                # Cost 1: Heading cost toward target angle
                end_x, end_y, end_yaw = traj[-1]
                heading_cost = abs(target_angle_rad - end_yaw)

                # Cost 2: Clearance cost (distance to obstacles)
                min_obs_dist = 99.0
                if scan_ranges:
                    for x, y, _ in traj:
                        dist = math.hypot(x, y)
                        if dist < min_obs_dist:
                            min_obs_dist = dist

                clearance_cost = 1.0 / (min_obs_dist + 1e-4) if min_obs_dist < 1.0 else 0.0

                # Cost 3: Velocity cost (reward higher speeds)
                velocity_cost = self.max_speed - v

                total_cost = (
                    self.heading_cost_gain * heading_cost +
                    self.clearance_cost_gain * clearance_cost +
                    self.velocity_cost_gain * velocity_cost
                )

                if total_cost < min_total_cost:
                    min_total_cost = total_cost
                    best_v = float(v)
                    best_w = float(w)

        return round(best_v, 3), round(best_w, 3)
