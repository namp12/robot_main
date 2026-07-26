#!/bin/bash
# setup_env.sh - Setup ROS2 workspace and serial permissions for new environment
# Usage: source setup_env.sh

set -e

echo "=== ROS2 Workspace Setup ==="

# 1. Source ROS2
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
    echo "[OK] Sourced ROS2 Humble"
else
    echo "[ERROR] ROS2 Humble not found at /opt/ros/humble"
    return 1
fi

# 2. Build workspace
echo ""
echo "=== Building workspace ==="
cd /home/robot/robot_ws
colcon build --packages-select robot_bringup robot_serial esp32_ros2_bridge --symlink-install

# 3. Source workspace
source install/setup.bash
echo "[OK] Sourced workspace"

# 4. Serial permissions
echo ""
echo "=== Setting up serial permissions ==="
sudo usermod -aG dialout $USER 2>/dev/null || true
echo "[OK] User added to dialout group"

# 5. Check ESP32
echo ""
echo "=== Checking ESP32 serial port ==="
if [ -e /dev/ttyACM0 ]; then
    echo "[OK] ESP32 found at /dev/ttyACM0"
elif [ -e /dev/ttyUSB0 ]; then
    echo "[OK] ESP32 found at /dev/ttyUSB0"
else
    echo "[WARN] ESP32 not detected. Connect ESP32 via USB."
fi

# 6. Check map directory
echo ""
echo "=== Checking map directory ==="
mkdir -p ~/robot_maps/my_room
if [ -f "$HOME/robot_maps/my_room/map.yaml" ]; then
    echo "[OK] Map exists at ~/robot_maps/my_room/map.yaml"
else
    echo "[INFO] No map found. Will need to run SLAM and save map."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Quick start commands:"
echo "  1. Run SLAM:     ros2 launch robot_bringup slam.launch.py"
echo "  2. Save map:     ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \"name: '\$HOME/robot_maps/my_room'\""
echo "  3. Copy map:     ros2 run robot_bringup save_map.py my_room"
echo "  4. Build:        colcon build --packages-select robot_bringup && source install/setup.bash"
echo "  5. Run Nav2:     ros2 launch robot_bringup nav2.launch.py"
echo ""
echo "Or run full pipeline: slam -> save_map -> copy_map -> build -> nav2"
