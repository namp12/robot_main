#!/bin/bash
# unmount_hdd.sh - Safely unmount the external HDD
#
# Usage:
#   bash unmount_hdd.sh

set -e

MOUNT_POINT="/mnt/robot_hdd"

if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
    echo "[INFO] $MOUNT_POINT is not mounted. Nothing to do."
    exit 0
fi

echo "[INFO] Syncing data..."
sync

echo "[INFO] Unmounting $MOUNT_POINT ..."
umount "$MOUNT_POINT"

echo "[OK] HDD safely unmounted."
