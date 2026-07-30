#!/bin/bash
# save_map.sh - Save the current SLAM map to a custom location or standard directory
#
# Usage:
#   bash save_map.sh                  # saves to ~/robot_maps/<timestamp>/
#   bash save_map.sh my_room          # saves to ~/robot_maps/my_room/
#   bash save_map.sh /path/to/folder  # saves to /path/to/folder/
#
# Prerequisites:
#   - SLAM Toolbox or Map Server must be running and publishing /map

set -e

# ---- Parse arguments ----
TARGET="${1:-$(date +%Y%m%d_%H%M%S)}"

# ---- Determine target directory ----
if [[ "$TARGET" == /* || "$TARGET" == \.* || "$TARGET" == ~* ]]; then
    # Expand ~ if present
    if [[ "$TARGET" == ~* ]]; then
        OUTPUT_DIR="${TARGET/#\~/$HOME}"
    else
        OUTPUT_DIR="$TARGET"
    fi
else
    MAPS_DIR="$HOME/robot_maps"
    OUTPUT_DIR="$MAPS_DIR/$TARGET"
fi

# ---- Create output directory ----
mkdir -p "$OUTPUT_DIR"

echo "[INFO] Saving map to: $OUTPUT_DIR"

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
    echo "  ros2 launch robot_bringup nav2.launch.py map:=$OUTPUT_DIR/map.yaml"
    echo ""
    ls -lh "$OUTPUT_DIR/"
else
    echo "[ERROR] Map save failed. Check that /map topic is publishing."
    echo "        Is SLAM Toolbox running?"
    exit 1
fi
