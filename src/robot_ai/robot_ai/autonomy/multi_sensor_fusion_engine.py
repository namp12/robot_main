import math
import numpy as np
from typing import Dict, Any, Optional, List, Tuple


class MultiSensorFusionEngine:
    """
    Multi-Sensor Fusion Perception Engine V5.0.
    Fuses data from 5 heterogeneous sensor streams:
    1. 2D LiDAR 360-degree LaserScan (/scan)
    2. Camera AI Vision YOLO11s Detections (/ai/detection)
    3. Ultrasound / IR Front & Rear Distance Sensors (/sensor/front_distance, /sensor/rear_distance)
    4. IMU 9-DOF Acceleration & Gyro Quaternion (/imu/data)
    5. Wheel Encoders & Odometry (/esp32/encoder_values, /odom)
    """

    def __init__(self, tilt_threshold_deg: float = 15.0, min_safe_distance_meters: float = 0.15):
        self.tilt_threshold_deg = tilt_threshold_deg
        self.min_safe_distance = min_safe_distance_meters

    def fuse_front_distance(self, lidar_min_front: float, ultrasonic_front_cm: float) -> float:
        """
        Fuse LiDAR front-sector minimum distance and Ultrasonic front distance (cm).
        Returns min safe front distance in meters.
        """
        ultrasonic_m = ultrasonic_front_cm / 100.0 if ultrasonic_front_cm > 0.0 else 99.0
        if lidar_min_front <= 0.05:
            lidar_m = 99.0
        else:
            lidar_m = lidar_min_front

        return round(float(min(lidar_m, ultrasonic_m)), 3)

    def check_imu_tilt_guard(self, roll_deg: float, pitch_deg: float) -> bool:
        """
        Returns True if IMU tilt angle exceeds safety threshold (>15 deg), indicating steep slope/tilt hazard.
        """
        return abs(roll_deg) > self.tilt_threshold_deg or abs(pitch_deg) > self.tilt_threshold_deg

    def fuse_perception_snapshot(
        self,
        scan_ranges: List[float],
        ultrasonic_front_cm: float,
        ultrasonic_rear_cm: float,
        ai_detections: List[Dict[str, Any]],
        roll_deg: float = 0.0,
        pitch_deg: float = 0.0
    ) -> Dict[str, Any]:
        """
        Fuses all 5 sensor streams into a unified perception snapshot.
        """
        # Calculate LiDAR front minimum distance
        lidar_front_min = 99.0
        if scan_ranges:
            num_pts = len(scan_ranges)
            front_indices = list(range(0, min(15, num_pts))) + list(range(max(0, num_pts - 15), num_pts))
            front_pts = [scan_ranges[i] for i in front_indices if 0.05 < scan_ranges[i] < 10.0]
            if front_pts:
                lidar_front_min = min(front_pts)

        fused_front_m = self.fuse_front_distance(lidar_front_min, ultrasonic_front_cm)
        tilt_hazard = self.check_imu_tilt_guard(roll_deg, pitch_deg)

        return {
            "fused_front_distance_meters": fused_front_m,
            "ultrasonic_front_cm": ultrasonic_front_cm,
            "ultrasonic_rear_cm": ultrasonic_rear_cm,
            "lidar_front_min_meters": round(float(lidar_front_min), 3),
            "tilt_hazard": tilt_hazard,
            "ai_detections": ai_detections or []
        }
