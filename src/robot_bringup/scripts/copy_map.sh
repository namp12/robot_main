#!/bin/bash
# copy_map.sh - Copy map from ~/robot_maps/my_room into ros2 package
# Usage: ./copy_map.sh [source_dir] [dest_dir]

set -e

SOURCE="${1:-$HOME/robot_maps/my_room}"
DEST="${2:-$(rospack find robot_bringup)/maps/my_room}"

if [ ! -d "$SOURCE" ]; then
    echo "Error: Source directory $SOURCE does not exist"
    exit 1
fi

mkdir -p "$DEST"

if [ -f "$SOURCE/map.yaml" ]; then
    cp "$SOURCE/map.yaml" "$DEST/map.yaml"
    echo "Copied map.yaml"
fi

if [ -f "$SOURCE/map.pgm" ]; then
    cp "$SOURCE/map.pgm" "$DEST/map.pgm"
    echo "Copied map.pgm"
fi

if [ ! -f "$DEST/map.yaml" ] || [ ! -f "$DEST/map.pgm" ]; then
    echo "Warning: map.yaml or map.pgm missing in destination"
    exit 1
fi

echo "Map successfully copied to: $DEST"
ls -la "$DEST"
