#!/bin/bash
# setup_env.sh - Environment configuration and quick aliases for Ubuntu PC
# Usage: source setup_env.sh

# Get directory where this script is located (works in bash and zsh)
if [ -n "$BASH_SOURCE" ]; then
    WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [ -n "$ZSH_VERSION" ]; then
    WORKSPACE_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
else
    WORKSPACE_DIR="$(pwd)"
fi

echo "============================================================"
echo "  🚀 [ROS 2 Ubuntu Environment] Initializing..."
echo "  📁 Workspace: $WORKSPACE_DIR"
echo "============================================================"

# 1. Source ROS 2 Base System
ROS_DISTRO_FOUND=""
for distro in humble jazzy iron rolling foxy; do
    if [ -f "/opt/ros/$distro/setup.bash" ]; then
        source "/opt/ros/$distro/setup.bash"
        ROS_DISTRO_FOUND="$distro"
        echo "  ✓ Sourced ROS 2 ($distro) from /opt/ros/$distro"
        break
    fi
done

if [ -z "$ROS_DISTRO_FOUND" ]; then
    echo "  ⚠️ [WARN] No ROS 2 installation found in /opt/ros/"
fi

# 2. Source Workspace Underlay/Overlay
if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash"
    echo "  ✓ Sourced workspace install/setup.bash"
else
    echo "  ℹ Workspace not built yet. Run 'robot_build' to build."
fi

# 3. Check Connected Robot Devices
echo ""
echo "--- Hardware Status Check ---"
if [ -e /dev/rplidar ]; then
    echo "  ✓ LiDAR ready:       /dev/rplidar -> $(readlink -f /dev/rplidar)"
elif ls /dev/ttyUSB* >/dev/null 2>&1; then
    echo "  ℹ LiDAR:            /dev/rplidar not bound (USB ports available: $(ls /dev/ttyUSB* | tr '\n' ' '))"
else
    echo "  ⚠️ LiDAR:            No RPLidar detected"
fi

if [ -e /dev/esp32 ]; then
    echo "  ✓ ESP32 ready:       /dev/esp32 -> $(readlink -f /dev/esp32)"
elif ls /dev/ttyACM* >/dev/null 2>&1; then
    echo "  ℹ ESP32:            /dev/esp32 not bound (ACM ports available: $(ls /dev/ttyACM* | tr '\n' ' '))"
else
    echo "  ⚠️ ESP32:            No ESP32 detected"
fi

if ls /dev/video* >/dev/null 2>&1; then
    echo "  ✓ Camera ready:      $(ls /dev/video0 2>/dev/null || ls /dev/video* | head -n 1)"
else
    echo "  ⚠️ Camera:           No /dev/video* found"
fi

# 4. Useful Helper Aliases for Ubuntu PC
alias robot_ws="cd '$WORKSPACE_DIR'"
alias robot_build="(cd '$WORKSPACE_DIR' && colcon build --symlink-install && source install/setup.bash)"
alias robot_clean="(cd '$WORKSPACE_DIR' && bash cleanup.sh --run)"
alias robot_rviz="ros2 launch robot_description display.launch.py"
alias robot_minimal="ros2 launch robot_bringup minimal.launch.py"
alias robot_full="ros2 launch robot_bringup full_robot.launch.py use_rviz:=true"
alias robot_slam="ros2 launch robot_bringup slam.launch.py"
alias robot_nav="ros2 launch robot_bringup nav2.launch.py"
alias robot_teleop="ros2 run teleop_twist_keyboard teleop_twist_keyboard"
alias robot_save_map="bash '$WORKSPACE_DIR/save_map.sh'"
alias robot_udev="bash '$WORKSPACE_DIR/scripts/setup_udev.sh'"

echo ""
echo "============================================================"
echo "  ✅ Environment ready! Shortcuts available:"
echo "    - robot_ws        : Đi đến thư mục workspace"
echo "    - robot_build     : Build workspace (colcon build --symlink-install)"
echo "    - robot_rviz      : Mở mô hình 3D RViz2 trên Ubuntu"
echo "    - robot_minimal   : Khởi chạy node phần cứng (LiDAR, ESP32, Cam)"
echo "    - robot_full      : Khởi chạy toàn bộ robot + RViz2"
echo "    - robot_slam      : Bật SLAM quét tạo bản đồ"
echo "    - robot_save_map  : Lưu bản đồ hiện tại"
echo "    - robot_nav       : Bật dẫn đường Nav2"
echo "    - robot_teleop    : Bàn phím điều khiển robot"
echo "    - robot_udev      : Cập nhật udev rules cho cổng USB"
echo "============================================================"
