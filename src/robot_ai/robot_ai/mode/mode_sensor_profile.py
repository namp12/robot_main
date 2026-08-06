from dataclasses import dataclass, field
from typing import List, Dict, Any
from robot_ai.mode_manager.mode_types import RobotMode


@dataclass
class ModeProfileConfig:
    mode: RobotMode
    mode_name: str
    camera_enabled: bool
    yolo_enabled: bool
    lidar_enabled: bool
    planner_enabled: bool
    active_modules: List[str]
    disabled_modules: List[str]


MODE_SENSOR_PROFILES: Dict[RobotMode, ModeProfileConfig] = {
    RobotMode.MANUAL: ModeProfileConfig(
        mode=RobotMode.MANUAL,
        mode_name="MANUAL",
        camera_enabled=False,
        yolo_enabled=False,
        lidar_enabled=False,
        planner_enabled=False,
        active_modules=["Web Joystick", "Keyboard Control", "Direct Wheel Output"],
        disabled_modules=["Local Planner", "Costmap", "Auto Explore", "Person Tracking", "Recovery", "Spatial Memory"]
    ),
    RobotMode.SAFE_MANUAL: ModeProfileConfig(
        mode=RobotMode.SAFE_MANUAL,
        mode_name="SAFE_MANUAL",
        camera_enabled=False,
        yolo_enabled=False,
        lidar_enabled=True,
        planner_enabled=False,
        active_modules=["Manual Joystick", "LiDAR Distance Safety Stop"],
        disabled_modules=["Local Planner", "Costmap", "Person Tracking", "Auto Explore"]
    ),
    RobotMode.FOLLOW_PERSON: ModeProfileConfig(
        mode=RobotMode.FOLLOW_PERSON,
        mode_name="FOLLOW_PERSON",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,  # Safety stop only
        planner_enabled=False,
        active_modules=["Camera AI", "YOLO Person Detection", "Person Tracking", "Safety Distance Stop"],
        disabled_modules=["Auto Explore", "Costmap", "Sector Planner", "Free Space Planner", "Recovery", "Dead End Memory"]
    ),
    RobotMode.FOLLOW_TARGET: ModeProfileConfig(
        mode=RobotMode.FOLLOW_TARGET,
        mode_name="FOLLOW_TARGET",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=False,
        active_modules=["Camera AI", "YOLO Target Tracking", "Target Follower"],
        disabled_modules=["Auto Explore", "Costmap", "Sector Planner", "Recovery"]
    ),
    RobotMode.AUTO_EXPLORE: ModeProfileConfig(
        mode=RobotMode.AUTO_EXPLORE,
        mode_name="AUTO_EXPLORE",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=True,
        active_modules=["LiDAR 360 Navigation", "Costmap", "Sector Planner", "Recovery", "Spatial Memory", "Camera AI Perception Fusion"],
        disabled_modules=["Person Tracking", "Manual Joystick", "Voice Session"]
    ),
    RobotMode.GO_TO_GOAL: ModeProfileConfig(
        mode=RobotMode.GO_TO_GOAL,
        mode_name="GO_TO_GOAL",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=True,
        active_modules=["Goal Planner", "Costmap", "Perception Fusion", "Recovery"],
        disabled_modules=["Person Tracking", "Manual Joystick"]
    ),
    RobotMode.PATROL: ModeProfileConfig(
        mode=RobotMode.PATROL,
        mode_name="PATROL",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=True,
        active_modules=["Waypoint Queue", "Planner", "Costmap", "Recovery"],
        disabled_modules=["Person Tracking", "Manual Joystick"]
    ),
    RobotMode.DELIVERY: ModeProfileConfig(
        mode=RobotMode.DELIVERY,
        mode_name="DELIVERY",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=True,
        active_modules=["Mission Queue", "Goal Planner", "QR Code Scanner"],
        disabled_modules=["Person Tracking", "Manual Joystick"]
    ),
    RobotMode.RETURN_HOME: ModeProfileConfig(
        mode=RobotMode.RETURN_HOME,
        mode_name="RETURN_HOME",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=True,
        active_modules=["Home Goal", "Planner", "Costmap", "Recovery"],
        disabled_modules=["Person Tracking", "Manual Joystick"]
    ),
    RobotMode.INSPECTION: ModeProfileConfig(
        mode=RobotMode.INSPECTION,
        mode_name="INSPECTION",
        camera_enabled=True,
        yolo_enabled=True,
        lidar_enabled=True,
        planner_enabled=False,
        active_modules=["Video Recording", "Diagnostic Logging", "Low Speed Crawler"],
        disabled_modules=["Person Tracking", "Auto Explore"]
    ),
    RobotMode.VOICE_ASSISTANT: ModeProfileConfig(
        mode=RobotMode.VOICE_ASSISTANT,
        mode_name="VOICE_ASSISTANT",
        camera_enabled=False,
        yolo_enabled=False,
        lidar_enabled=False,
        planner_enabled=False,
        active_modules=["PhoWhisper STT", "Ollama LLM", "TTS Audio Engine"],
        disabled_modules=["Planner", "Costmap", "Auto Explore", "Person Tracking", "Wheel Movement"]
    ),
    RobotMode.DOCKING: ModeProfileConfig(
        mode=RobotMode.DOCKING,
        mode_name="DOCKING",
        camera_enabled=True,
        yolo_enabled=False,
        lidar_enabled=True,
        planner_enabled=True,
        active_modules=["Docking Marker Alignment", "Low Speed Precision Control"],
        disabled_modules=["Person Tracking", "Auto Explore"]
    ),
    RobotMode.SIMULATION: ModeProfileConfig(
        mode=RobotMode.SIMULATION,
        mode_name="SIMULATION",
        camera_enabled=False,
        yolo_enabled=False,
        lidar_enabled=False,
        planner_enabled=True,
        active_modules=["Dry Run Simulation Engine"],
        disabled_modules=["Physical Motors"]
    ),
    RobotMode.EMERGENCY_STOP: ModeProfileConfig(
        mode=RobotMode.EMERGENCY_STOP,
        mode_name="EMERGENCY_STOP",
        camera_enabled=False,
        yolo_enabled=False,
        lidar_enabled=False,
        planner_enabled=False,
        active_modules=["Emergency Brake System"],
        disabled_modules=["All Autonomous & Manual Motion"]
    ),
}


def get_sensor_profile(mode: RobotMode) -> ModeProfileConfig:
    return MODE_SENSOR_PROFILES.get(mode, MODE_SENSOR_PROFILES[RobotMode.MANUAL])
