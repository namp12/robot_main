#!/bin/bash
# mount_hdd.sh - Mount external HDD to /mnt/robot_hdd
#
# Usage:
#   sudo bash mount_hdd.sh              # auto-detect and mount first USB drive
#   sudo bash mount_hdd.sh /dev/sda1    # mount specific partition
#
# This script:
#   1. Creates the mount point if it doesn't exist
#   2. Detects the external HDD (or uses the provided device)
#   3. Mounts it to /mnt/robot_hdd
#   4. Creates the maps/ directory on the HDD
#
# For auto-mount on boot, see setup_hdd_automount.sh

set -e

MOUNT_POINT="/mnt/robot_hdd"

# ---- Determine device ----
if [ -n "$1" ]; then
    DEVICE="$1"
else
    # Auto-detect: find the first USB block device (typically /dev/sda1)
    DEVICE=$(lsblk -dpno NAME,TRAN | grep 'usb' | head -1 | awk '{print $1}')
    if [ -z "$DEVICE" ]; then
        echo "[ERROR] No USB drive detected."
        echo "        Plug in the HDD and run again, or specify device:"
        echo "        sudo bash mount_hdd.sh /dev/sda1"
        echo ""
        echo "Available block devices:"
        lsblk -dpno NAME,SIZE,TRAN,MOUNTPOINT
        exit 1
    fi
    echo "[INFO] Detected USB device: $DEVICE"
fi

# ---- Check if device exists ----
if [ ! -b "$DEVICE" ]; then
    echo "[ERROR] Device $DEVICE not found."
    echo "        Run 'lsblk' to see available devices."
    lsblk -dpno NAME,SIZE,TRAN,MOUNTPOINT
    exit 1
fi

# ---- Check if already mounted ----
if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
    echo "[INFO] $MOUNT_POINT is already mounted."
    ls -la "$MOUNT_POINT"
    exit 0
fi

# ---- Create mount point ----
mkdir -p "$MOUNT_POINT"
echo "[INFO] Mount point: $MOUNT_POINT"

# ---- Mount ----
echo "[INFO] Mounting $DEVICE -> $MOUNT_POINT ..."
mount "$DEVICE" "$MOUNT_POINT"

# ---- Set ownership so 'robot' user can write ----
chown -R robot:robot "$MOUNT_POINT"
chmod -R 775 "$MOUNT_POINT"

# ---- Create maps directory ----
mkdir -p "$MOUNT_POINT/maps"
echo "[INFO] Created $MOUNT_POINT/maps/"

# ---- Done ----
echo ""
echo "[OK] HDD mounted successfully."
echo "     Mount point: $MOUNT_POINT"
echo "     Maps dir:    $MOUNT_POINT/maps/"
echo ""
df -h "$MOUNT_POINT"
