# vision_ai_node

AI Vision node for ROS2 Humble. Subscribes to camera images and runs YOLO object detection.

## Architecture

```
camera_node --> /camera/image_raw --> vision_ai_node --> /vision/detections
                                                       --> /vision/annotated_image
                                                       --> /vision/status
```

- **Does NOT open webcam** - receives frames via ROS2 topic from `camera_node`
- YOLO inference runs at throttled FPS (default 5) to save CPU
- Skips AI if no subscribers are listening

## Dependencies

```bash
# ROS2 packages
sudo apt install ros-humble-cv-bridge ros-humble-sensor-msgs python3-opencv

# YOLO (ultralytics)
pip3 install ultralytics
```

## Build

```bash
cd ~/robot_ws
colcon build --packages-select vision_ai_node
source install/setup.bash
```

## Run

```bash
# Start with detection disabled (idle mode):
ros2 launch vision_ai_node vision_ai.launch.py

# Enable detection with a model:
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/home/robot/robot_ws/src/vision_ai_node/models/yolov8n.pt

# Custom confidence and FPS:
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/path/to/yolov8n.pt \
  confidence_threshold:=0.3 \
  max_fps:=3.0

# Disable annotated image publishing (save bandwidth):
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/path/to/yolov8n.pt \
  publish_image:=false
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_detection` | bool | false | Enable YOLO inference |
| `confidence_threshold` | float | 0.5 | Min confidence [0.0-1.0] |
| `max_fps` | float | 5.0 | Max AI processing rate |
| `model_path` | string | "" | Path to YOLO .pt model |
| `publish_image` | bool | true | Publish annotated images |

## Change Model

Place your `.pt` model in `models/` directory, then:

```bash
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/home/robot/robot_ws/src/vision_ai_node/models/your_model.pt
```

## Check Topics

```bash
# List topics
ros2 topic list

# View detections
ros2 topic echo /vision/detections

# View status
ros2 topic echo /vision/status

# View annotated image (on laptop with GUI)
ros2 run rqt_image_view rqt_image_view
# Select /vision/annotated_image
```

## Full System (camera + AI)

```bash
# Terminal 1: Start camera
ros2 launch camera_node camera.launch.py

# Terminal 2: Start AI
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/home/robot/robot_ws/src/vision_ai_node/models/yolov8n.pt
```

## Download YOLOv8n Model

```bash
# On laptop with internet, then copy to RPi:
pip3 install ultralytics
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
# Copy yolov8n.pt to RPi: models/yolov8n.pt
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "ultralytics not found" | `pip3 install ultralytics` |
| "model not loaded" | Check `model_path` parameter points to valid .pt file |
| No detections | Lower `confidence_threshold` (e.g. 0.3) |
| High CPU | Lower `max_fps` (e.g. 2.0) or use `yolov8n` (nano) |
| No frames | Check `camera_node` is running and publishing |
