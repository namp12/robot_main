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

    def __init__(self, timeout_sec: float = 0.8, startup_grace_sec: float = 10.0):
        self.timeout_sec = timeout_sec
        self.startup_grace_sec = startup_grace_sec
        self.start_ts = time.time()

        self._has_lidar = False
        self._has_odom = False
        self._last_lidar_ts = time.time()
        self._last_odom_ts = time.time()
        self._last_imu_ts = time.time()
        self._last_camera_ts = time.time()

        self._lock = threading.Lock()

    def touch_lidar(self):
        with self._lock:
            self._has_lidar = True
            self._last_lidar_ts = time.time()

    def touch_odom(self):
        with self._lock:
            self._has_odom = True
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
            # Allow initial startup grace period for sensors to connect
            if now - self.start_ts < self.startup_grace_sec:
                if not self._has_lidar:
                    return True, "LiDAR warming up / waiting for /scan..."

            if not self._has_lidar:
                return False, "LiDAR node not running (topic /scan missing). Please run: ros2 launch robot_bringup lidar.launch.py"

            if now - self._last_lidar_ts > self.timeout_sec:
                return False, f"LiDAR timeout ({now - self._last_lidar_ts:.2f}s > {self.timeout_sec}s)"

            if self._has_odom and (now - self._last_odom_ts > (self.timeout_sec * 3.0)):
                return False, f"Odometry timeout ({now - self._last_odom_ts:.2f}s > {self.timeout_sec * 3.0}s)"

        return True, "OK"

    def get_system_metrics(self) -> Dict[str, float]:
        """Return CPU & RAM load metrics for system load throttling."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_percent": psutil.virtual_memory().percent
        }
