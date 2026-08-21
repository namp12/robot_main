#!/bin/bash
# save_map.sh - Save SLAM occupancy grid map to YAML & PGM
# Usage: bash save_map.sh [optional_target_path]

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_PATH=${1:-"$WORKSPACE_DIR/src/robot_bringup/maps/phong_demo"}

# Detect & source ROS 2
for distro in humble jazzy iron rolling foxy; do
    if [ -f "/opt/ros/$distro/setup.bash" ]; then
        source "/opt/ros/$distro/setup.bash"
        break
    fi
done

if [ -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    source "$WORKSPACE_DIR/install/setup.bash" 2>/dev/null
fi

python3 "$WORKSPACE_DIR/scripts/save_map.py" "$TARGET_PATH"
