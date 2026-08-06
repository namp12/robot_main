import logging
from typing import Dict, Any, Tuple

from robot_ai.feature.feature_base import FeatureBase
from robot_ai.mode_manager.mode_types import RobotMode
from robot_ai.mode.mode_sensor_profile import ModeProfileConfig
from robot_ai.feature.follow_person_engine import FollowPersonEngine
from robot_ai.feature.auto_explore_engine import AutoExploreEngine

logger = logging.getLogger("FeatureV2Implementations")


class FollowPersonFeature(FeatureBase):
    """
    Dedicated V2 Feature implementation for FOLLOW_PERSON.
    Enforces complete feature isolation:
    - Active: Camera AI, YOLO11, Person Tracker, Target Lock, Safety Controller.
    - Disabled: Planner, Navigation, Costmap, Recovery, Spatial Memory, Auto Explore.
    - LiDAR Safety ONLY (< 0.40m -> STOP).
    """

    def __init__(self):
        super().__init__("FOLLOW_PERSON")
        self.mode = RobotMode.FOLLOW_PERSON
        self.engine = FollowPersonEngine()
        self.profile = ModeProfileConfig(
            mode=RobotMode.FOLLOW_PERSON,
            sensor_camera=True,
            sensor_lidar=True,  # Safety only
            sensor_ultrasonic=True,
            sensor_imu=True,
            sensor_wheel_encoder=True,
            active_modules=[
                "Camera Node", "YOLO11", "Person Detection", "Multi Object Tracker",
                "Target Lock", "Target Filter", "Distance Estimator", "Motion Controller",
                "Heading PID", "Distance PID", "Safety Controller", "Wheel Controller"
            ],
            disabled_modules=[
                "Planner", "Navigation", "Costmap", "Recovery", "Spatial Memory",
                "Sector Planner", "Goal Planner", "Mission Queue", "Waypoint",
                "Manual Controller", "Joystick", "Voice Session", "Auto Explore"
            ]
        )

    def on_initialize(self) -> bool:
        logger.info("⚙️ [INIT V2] Initialized Isolated Feature 'FOLLOW_PERSON'")
        self.engine.reset()
        return True

    def on_start(self) -> bool:
        logger.info("🟢 [START V2] Activated Isolated Feature 'FOLLOW_PERSON'")
        logger.info(f"   Active Modules: {self.profile.active_modules}")
        logger.info(f"   Disabled Modules: {self.profile.disabled_modules}")
        self.engine.reset()
        return True

    def on_pause(self) -> bool:
        logger.info("⏸️ [PAUSE V2] Paused Feature 'FOLLOW_PERSON'")
        return True

    def on_resume(self) -> bool:
        logger.info("▶️ [RESUME V2] Resumed Feature 'FOLLOW_PERSON'")
        return True

    def on_stop(self) -> bool:
        logger.info("🔴 [STOP V2] Stopped Feature 'FOLLOW_PERSON'")
        self.engine.reset()
        return True

    def on_cleanup(self) -> bool:
        logger.info("🧹 [CLEANUP V2] Cleaned up Feature 'FOLLOW_PERSON' background tasks & target locks")
        self.engine.reset()
        return True

    def on_release(self) -> bool:
        logger.info("🔓 [RELEASE V2] Released Feature 'FOLLOW_PERSON' resources")
        return True

    def process_cycle(self, perception_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        return self.engine.process_cycle(perception_data)


class AutoExploreFeature(FeatureBase):
    """
    Dedicated V2 Feature implementation for AUTO_EXPLORE.
    Enforces complete feature isolation:
    - Active: LiDAR Driver, Obstacle Detector, Camera Fusion, Costmap, 36 Sector Planner, Velocity Planner, Recovery, Spatial Memory, Health Watchdog.
    - Disabled: YOLO Tracking, Person Tracker, Target Lock, Follow Person Controller.
    """

    def __init__(self):
        super().__init__("AUTO_EXPLORE")
        self.mode = RobotMode.AUTO_EXPLORE
        self.engine = AutoExploreEngine()
        self.profile = ModeProfileConfig(
            mode=RobotMode.AUTO_EXPLORE,
            sensor_camera=True,
            sensor_lidar=True,
            sensor_ultrasonic=True,
            sensor_imu=True,
            sensor_wheel_encoder=True,
            active_modules=[
                "LiDAR Driver", "Obstacle Detector", "Camera Fusion", "Perception Fusion",
                "Costmap", "Sector Planner", "Local Planner", "Velocity Planner",
                "Recovery", "Spatial Memory", "Dead End Memory", "Visited Memory", "Health Watchdog"
            ],
            disabled_modules=[
                "YOLO Tracking", "Person Tracker", "Target Lock", "Manual Controller",
                "Joystick", "Voice Session", "Mission Queue"
            ]
        )

    def on_initialize(self) -> bool:
        logger.info("⚙️ [INIT V2] Initialized Isolated Feature 'AUTO_EXPLORE'")
        self.engine.reset()
        return True

    def on_start(self) -> bool:
        logger.info("🟢 [START V2] Activated Isolated Feature 'AUTO_EXPLORE'")
        logger.info(f"   Active Modules: {self.profile.active_modules}")
        logger.info(f"   Disabled Modules: {self.profile.disabled_modules}")
        self.engine.reset()
        return True

    def on_pause(self) -> bool:
        logger.info("⏸️ [PAUSE V2] Paused Feature 'AUTO_EXPLORE'")
        return True

    def on_resume(self) -> bool:
        logger.info("▶️ [RESUME V2] Resumed Feature 'AUTO_EXPLORE'")
        return True

    def on_stop(self) -> bool:
        logger.info("🔴 [STOP V2] Stopped Feature 'AUTO_EXPLORE'")
        self.engine.reset()
        return True

    def on_cleanup(self) -> bool:
        logger.info("🧹 [CLEANUP V2] Cleaned up Feature 'AUTO_EXPLORE' background planners & spatial memory")
        self.engine.reset()
        return True

    def on_release(self) -> bool:
        logger.info("🔓 [RELEASE V2] Released Feature 'AUTO_EXPLORE' resources")
        return True

    def process_cycle(self, perception_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        return self.engine.process_cycle(perception_data)
