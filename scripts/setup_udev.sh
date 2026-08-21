#!/bin/bash
# scripts/setup_udev.sh - Install and apply udev rules for ESP32 and RPLidar
# Usage: bash scripts/setup_udev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RULES_FILE="$WORKSPACE_DIR/udev/99-robot-usb.rules"

echo "============================================================"
echo "  [Robot Setup] Configuring Udev Rules for Ubuntu"
echo "============================================================"

if [ ! -f "$RULES_FILE" ]; then
    echo "[ERROR] Rules file not found at: $RULES_FILE"
    exit 1
fi

echo "[1/4] Copying udev rules to /etc/udev/rules.d/ ..."
sudo cp "$RULES_FILE" /etc/udev/rules.d/99-robot-usb.rules

echo "[2/4] Setting user permissions for serial, video, and audio..."
CURRENT_USER="${SUDO_USER:-$USER}"
sudo usermod -aG dialout,video,audio "$CURRENT_USER"
echo "  ✓ Added user '$CURRENT_USER' to groups: dialout, video, audio"

echo "[3/4] Reloading and triggering udev daemon..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "  ✓ Udev daemon updated successfully"

echo "[4/4] Checking connected robot devices..."
echo "--- Serial Links ---"
if [ -e /dev/rplidar ]; then
    echo "  ✓ /dev/rplidar -> $(readlink -f /dev/rplidar)"
else
    echo "  ℹ /dev/rplidar: Not connected or different vendor ID"
fi

if [ -e /dev/esp32 ]; then
    echo "  ✓ /dev/esp32 -> $(readlink -f /dev/esp32)"
else
    echo "  ℹ /dev/esp32: Not connected or different vendor ID"
fi

echo ""
echo "--- Video Devices (Cameras) ---"
ls -l /dev/video* 2>/dev/null || echo "  ℹ No video devices found"

echo ""
echo "--- All USB / ACM Serial Ports ---"
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "  ℹ No ttyUSB / ttyACM devices found"

echo ""
echo "============================================================"
echo "  ✓ Udev configuration completed!"
echo "  Note: If this is the first time adding group permissions,"
echo "  please log out and log back in (or run 'newgrp dialout')."
echo "============================================================"
