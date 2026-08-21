#!/bin/bash
# setup_ubuntu.sh - One-click environment installer & setup for Ubuntu PC (ROS 2)
# Usage: bash setup_ubuntu.sh

set -e

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "   🤖 ROBOT WORKSPACE SETUP FOR UBUNTU (ROS 2)"
echo "   Workspace: $WORKSPACE_DIR"
echo "============================================================"

# 1. Detect Ubuntu version and ROS 2 Distro
UBUNTU_CODENAME=$(lsb_release -cs 2>/dev/null || echo "jammy")
if [ -z "$ROS_DISTRO" ]; then
    if [ "$UBUNTU_CODENAME" = "noble" ] || [ -d "/opt/ros/jazzy" ]; then
        ROS_DISTRO="jazzy"
    else
        ROS_DISTRO="humble"
    fi
fi

echo "[1/6] Detected Environment:"
echo "  - OS: $(lsb_release -ds 2>/dev/null || uname -s)"
echo "  - Target ROS 2 Distro: $ROS_DISTRO"

if [ ! -d "/opt/ros/$ROS_DISTRO" ]; then
    echo ""
    echo "[WARN] ROS 2 ($ROS_DISTRO) not found in /opt/ros/$ROS_DISTRO."
    echo "  Please install ROS 2 Desktop first:"
    echo "  https://docs.ros.org/en/$ROS_DISTRO/Installation/Ubuntu-Install-Debians.html"
    echo ""
    read -p "Do you want to continue installing system tools and Python packages? [y/N]: " proceed
    if [[ ! "$proceed" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. System and ROS 2 APT packages
echo ""
echo "[2/6] Installing ROS 2 packages and build tools..."
sudo apt-get update -qq

sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    v4l-utils \
    alsa-utils \
    pulseaudio-utils || true

if [ -d "/opt/ros/$ROS_DISTRO" ]; then
    sudo apt-get install -y \
        ros-$ROS_DISTRO-slam-toolbox \
        ros-$ROS_DISTRO-navigation2 \
        ros-$ROS_DISTRO-nav2-bringup \
        ros-$ROS_DISTRO-robot-localization \
        ros-$ROS_DISTRO-joint-state-publisher \
        ros-$ROS_DISTRO-joint-state-publisher-gui \
        ros-$ROS_DISTRO-robot-state-publisher \
        ros-$ROS_DISTRO-rviz2 \
        ros-$ROS_DISTRO-cv-bridge \
        ros-$ROS_DISTRO-image-transport \
        ros-$ROS_DISTRO-laser-filters \
        ros-$ROS_DISTRO-xacro \
        ros-$ROS_DISTRO-teleop-twist-keyboard \
        ros-$ROS_DISTRO-tf2-ros \
        ros-$ROS_DISTRO-tf2-geometry-msgs || true
fi

# 3. Rosdep init & update
echo ""
echo "[3/6] Initializing and updating rosdep..."
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init 2>/dev/null || true
fi
rosdep update --include-eol-distros 2>/dev/null || true

# 4. Install Python dependencies
echo ""
echo "[4/6] Installing Python packages for Robot AI, Serial & Web..."
pip3 install -q --upgrade pip || true
pip3 install -q \
    pyserial \
    numpy \
    opencv-python \
    ultralytics \
    fastapi \
    uvicorn \
    websockets \
    pyttsx3 \
    pygame \
    requests \
    aiohttp || true

# 5. Setup Udev Rules & User Groups
echo ""
echo "[5/6] Setting up Udev rules and hardware permissions..."
if [ -f "$WORKSPACE_DIR/scripts/setup_udev.sh" ]; then
    bash "$WORKSPACE_DIR/scripts/setup_udev.sh"
fi

# 6. Build Workspace
echo ""
echo "[6/6] Building ROS 2 workspace..."
if [ -d "/opt/ros/$ROS_DISTRO" ]; then
    source /opt/ros/$ROS_DISTRO/setup.bash
    cd "$WORKSPACE_DIR"
    colcon build --symlink-install
    echo "  ✓ Workspace built successfully!"
fi

echo ""
echo "============================================================"
echo "  🎉 UBUNTU ROS 2 SETUP HOÀN TẤT!"
echo "============================================================"
echo "  Để bắt đầu làm việc trong mỗi terminal mới, chỉ cần chạy:"
echo "    source setup_env.sh"
echo ""
echo "  Các lệnh tắt nhanh có sẵn sau khi source setup_env.sh:"
echo "    robot_build   -> Build lại toàn bộ workspace với symlink"
echo "    robot_rviz    -> Mở RViz2 hiển thị 3D robot model"
echo "    robot_slam    -> Chạy toàn bộ stack SLAM tạo bản đồ"
echo "    robot_nav     -> Chạy Nav2 dẫn đường tự động"
echo "    robot_teleop  -> Điều khiển robot bằng bàn phím"
echo "============================================================"
