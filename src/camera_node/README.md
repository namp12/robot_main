# camera_node

USB Webcam driver node for ROS2 Humble. Captures frames from a UVC webcam and publishes them as ROS2 topics.

## Features

- Publishes raw camera images to `/camera/image_raw`
- Publishes camera metadata to `/camera/camera_info`
- Configurable resolution, FPS, device index via ROS2 parameters
- Auto-reconnect if camera is unplugged (no restart needed)
- Clean shutdown (no "Device Busy" on restart)
- Low CPU/RAM usage, suitable for Raspberry Pi 4

## Dependencies

```bash
sudo apt install ros-humble-cv-bridge ros-humble-sensor-msgs python3-opencv
```

## Build

```bash
cd ~/robot_ws
colcon build --packages-select camera_node
source install/setup.bash
```

## Run

```bash
# Default (camera 0, 640x480, 15 FPS)
ros2 launch camera_node camera.launch.py

# Custom camera index
ros2 launch camera_node camera.launch.py camera_index:=2

# Custom resolution
ros2 launch camera_node camera.launch.py width:=1280 height:=720

# Custom FPS
ros2 launch camera_node camera.launch.py fps:=30.0

# Run node directly (without launch file)
ros2 run camera_node camera_node
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `camera_index` | int | 0 | V4L2 device index (0 = /dev/video0) |
| `width` | int | 640 | Frame width in pixels |
| `height` | int | 480 | Frame height in pixels |
| `fps` | double | 15.0 | Target frames per second |
| `frame_id` | string | camera_link | TF frame ID in message headers |

## Check Topics

```bash
# List topics
ros2 topic list

# View image info
ros2 topic echo /camera/image_raw --once

# View camera info
ros2 topic echo /camera/camera_info --once

# Visual check (on laptop with GUI)
ros2 run rqt_image_view rqt_image_view
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot open camera" | Check `ls /dev/video*`, try different `camera_index` |
| "Device Busy" | Another node is using the camera: `fuser /dev/video0` |
| Low FPS on RPi | Lower resolution or FPS: `fps:=10.0 width:=320 height:=240` |
| No `/camera/image_raw` | Check `ros2 topic list`, verify node is running |
