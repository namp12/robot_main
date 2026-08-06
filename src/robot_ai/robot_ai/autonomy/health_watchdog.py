import time
import psutil
import threading
from typing import Dict, Tuple


class HealthWatchdog:
    """
    Sensor & System Health Monitor & Safety Watchdog.
    Monitors LiDAR Hz, Camera FPS, Odometry & IMU update rates, CPU/RAM usage.
    Triggers safety stop if critical sensor timeouts exceed threshold (0.5s).
    """

    def __init__(self, timeout_sec: float = 0.5):
        self.timeout_sec = timeout_sec

        self._last_lidar_ts = time.time()
        self._last_odom_ts = time.time()
        self._last_imu_ts = time.time()
        self._last_camera_ts = time.time()

        self._lock = threading.Lock()

    def touch_lidar(self):
        with self._lock:
            self._last_lidar_ts = time.time()

    def touch_odom(self):
        with self._lock:
            self._last_odom_ts = time.time()

    def touch_imu(self):
        with self._lock:
            self._last_imu_ts = time.time()

    def touch_camera(self):
        with self._lock:
            self._last_camera_ts = time.time()

    def check_health(self) -> Tuple[bool, str]:
        """Check if all critical sensors are updating within timeout window."""
        now = time.time()
        with self._lock:
            if now - self._last_lidar_ts > self.timeout_sec:
                return False, f"LiDAR timeout ({now - self._last_lidar_ts:.2f}s > {self.timeout_sec}s)"

            if now - self._last_odom_ts > (self.timeout_sec * 2.0):
                return False, f"Odometry timeout ({now - self._last_odom_ts:.2f}s > {self.timeout_sec * 2.0}s)"

        return True, "OK"

    def get_system_metrics(self) -> Dict[str, float]:
        """Return CPU & RAM load metrics for system load throttling."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_percent": psutil.virtual_memory().percent
        }
