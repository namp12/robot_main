#!/bin/bash
# setup_hdd_automount.sh - Configure auto-mount for the external HDD on boot
#
# Usage:
#   sudo bash setup_hdd_automount.sh              # auto-detect UUID
#   sudo bash setup_hdd_automount.sh <UUID>       # specify UUID manually
#
# This adds an entry to /etc/fstab so the HDD mounts automatically
# every time the Raspberry Pi boots.
#
# To find your HDD UUID:  sudo blkid
# To undo:  sudo bash setup_hdd_automount.sh --remove

set -e

MOUNT_POINT="/mnt/robot_hdd"
FSTAB="/etc/fstab"

# ---- Remove mode ----
if [ "$1" = "--remove" ]; then
    echo "[INFO] Removing automount entry from $FSTAB ..."
    sed -i '\|# robot_hdd_automount|d' "$FSTAB"
    echo "[OK] Entry removed. Run 'sudo umount $MOUNT_POINT' to unmount."
    exit 0
fi

# ---- Get UUID ----
if [ -n "$1" ]; then
    UUID="$1"
else
    # Find the first USB device partition
    DEVICE=$(lsblk -dpno NAME,TRAN | grep 'usb' | head -1 | awk '{print $1}')
    if [ -z "$DEVICE" ]; then
        echo "[ERROR] No USB drive detected. Plug in the HDD first."
        exit 1
    fi
    UUID=$(blkid -s UUID -o value "$DEVICE")
    if [ -z "$UUID" ]; then
        echo "[ERROR] Could not read UUID from $DEVICE"
        echo "        Try: sudo blkid $DEVICE"
        exit 1
    fi
    FSTYPE=$(blkid -s TYPE -o value "$DEVICE")
    echo "[INFO] Device:  $DEVICE"
    echo "[INFO] UUID:    $UUID"
    echo "[INFO] FS Type: $FSTYPE"
fi

# ---- Check if already in fstab ----
if grep -q "robot_hdd_automount" "$FSTAB" 2>/dev/null; then
    echo "[WARN] An automount entry already exists in $FSTAB"
    echo "       Remove it first with: sudo bash $0 --remove"
    grep "robot_hdd_automount" "$FSTAB"
    exit 1
fi

# ---- Create mount point ----
mkdir -p "$MOUNT_POINT"

# ---- Default filesystem type ----
FSTYPE="${FSTYPE:-ext4}"

# ---- Add fstab entry ----
# nofail: don't fail boot if HDD is not plugged in
# uid/gid: robot user can read/write
ROBOT_UID=$(id -u robot 2>/dev/null || echo 1000)
ROBOT_GID=$(id -g robot 2>/dev/null || echo 1000)

echo "" >> "$FSTAB"
echo "# robot_hdd_automount - External HDD for robot maps" >> "$FSTAB"
echo "UUID=$UUID  $MOUNT_POINT  $FSTYPE  defaults,nofail,uid=$ROBOT_UID,gid=$ROBOT_GID  0  2" >> "$FSTAB"

echo ""
echo "[OK] Auto-mount configured!"
echo "     The HDD will mount automatically on every boot."
echo "     Mount point: $MOUNT_POINT"
echo ""
echo "Added to $FSTAB:"
grep "robot_hdd_automount" "$FSTAB"
echo ""
echo "To test without rebooting:"
echo "  sudo mount -a"
echo ""
echo "To remove automount:"
echo "  sudo bash $0 --remove"
