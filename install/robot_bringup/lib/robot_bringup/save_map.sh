#!/bin/bash
# save_map.sh - Save the current SLAM map to the external HDD
#
# Usage:
#   bash save_map.sh                  # saves to /mnt/robot_hdd/maps/<timestamp>/
#   bash save_map.sh my_room          # saves to /mnt/robot_hdd/maps/my_room/
#   bash save_map.sh my_room --auto   # also auto-detects and mounts HDD first
#
# Prerequisites:
#   - SLAM Toolbox must be running and publishing /map
#   - External HDD must be mounted (or use --auto flag)

set -e

# ---- Configuration ----
HDD_MOUNT="/mnt/robot_hdd"
MAPS_DIR="$HDD_MOUNT/maps"

# ---- Parse arguments ----
MAP_NAME="${1:-$(date +%Y%m%d_%H%M%S)}"
AUTO_MOUNT=false

for arg in "$@"; do
    if [ "$arg" = "--auto" ]; then
        AUTO_MOUNT=true
    fi
done

# ---- Auto-mount if requested ----
if [ "$AUTO_MOUNT" = true ]; then
    if ! mountpoint -q "$HDD_MOUNT" 2>/dev/null; then
        echo "[INFO] HDD not mounted. Attempting auto-mount..."
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        sudo bash "$SCRIPT_DIR/mount_hdd.sh"
    fi
fi

# ---- Check HDD is mounted ----
if ! mountpoint -q "$HDD_MOUNT" 2>/dev/null; then
    echo "[ERROR] External HDD is not mounted at $HDD_MOUNT"
    echo ""
    echo "Options:"
    echo "  1. Plug in the HDD and run:  sudo bash $(dirname "$0")/mount_hdd.sh"
    echo "  2. Or use --auto flag:       bash save_map.sh my_room --auto"
    exit 1
fi

# ---- Create output directory ----
OUTPUT_DIR="$MAPS_DIR/$MAP_NAME"
mkdir -p "$OUTPUT_DIR"

echo "[INFO] Saving map to: $OUTPUT_DIR"
echo "[INFO] Map name: $MAP_NAME"

# ---- Source ROS2 ----
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
fi
if [ -f ~/robot_ws/install/setup.bash ]; then
    source ~/robot_ws/install/setup.bash
fi

# ---- Save map ----
ros2 run nav2_map_server map_saver_cli \
    -f "$OUTPUT_DIR/map" \
    --ros-args -p save_map_timeout:=10.0

# ---- Verify ----
if [ -f "$OUTPUT_DIR/map.yaml" ] && [ -f "$OUTPUT_DIR/map.pgm" ]; then
    echo ""
    echo "[OK] Map saved successfully!"
    echo "     YAML: $OUTPUT_DIR/map.yaml"
    echo "     PGM:  $OUTPUT_DIR/map.pgm"
    echo ""
    echo "To load this map:"
    echo "  ros2 launch robot_bringup localization.launch.py map:=$OUTPUT_DIR/map.yaml"
    echo ""
    ls -lh "$OUTPUT_DIR/"
else
    echo "[ERROR] Map save failed. Check that /map topic is publishing."
    echo "        Is SLAM Toolbox running?"
    exit 1
fi
