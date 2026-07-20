# robot_ai

AI Vision module for ROS2 Humble. YOLO object detection with ONNX Runtime, optimized for Raspberry Pi 4.

## Architecture

```
camera_node --> /camera/image_raw --> robot_ai (CameraManager)
                                          |
                                    [inference timer 5 FPS]
                                          |
                                     Detector (YOLO)
                                          |
                              /robot/ai/detections (DetectionArray)
                              /robot/ai/status     (AIStatus)
```

### Modular Design

| Module | File | Responsibility |
|--------|------|----------------|
| Config | `config.py` | Parameters, validation, defaults |
| Model | `model_loader.py` | ONNX/PyTorch model loading |
| Detector | `detector.py` | Pre-processing, inference, NMS |
| Camera | `camera.py` | Frame subscription, storage |
| Publisher | `publisher.py` | ROS2 message publishing |
| Node | `ai_node.py` | Orchestration, timers, lifecycle |

### Extensibility

Each module is independent. Add new capabilities without modifying existing code:
- **ByteTrack**: Add `tracker.py` module
- **OCR**: Add `ocr.py` module
- **Face Recognition**: Add `face.py` module
- **QR Detection**: Add `qr.py` module

## Dependencies

```bash
# Required
sudo apt install ros-humble-cv-bridge ros-humble-sensor-msgs python3-opencv

# ONNX Runtime (preferred - lower RAM ~150MB)
pip3 install onnxruntime

# OR Ultralytics (fallback - higher RAM ~400MB)
pip3 install ultralytics
```

## Model Preparation

### Option 1: Export YOLOv11n to ONNX (recommended)

```bash
# On laptop with internet
pip3 install ultralytics
python3 -c "
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.export(format='onnx', imgsz=640, simplify=True)
"
# Copy yolo11n.onnx to RPi: ~/robot_ws/src/robot_ai/model/
```

### Option 2: Use .pt directly (higher RAM)

```bash
# Copy yolo11n.pt to RPi: ~/robot_ws/src/robot_ai/model/
```

## Build

```bash
cd ~/robot_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select robot_ai
source install/setup.bash
```

## Run

```bash
# With ONNX model
ros2 launch robot_ai ai.launch.py model_path:=/home/robot/robot_ws/src/robot_ai/model/yolo11n.onnx

# With .pt model (fallback to ultralytics)
ros2 launch robot_ai ai.launch.py model_path:=/home/robot/robot_ws/src/robot_ai/model/yolo11n.pt

# Custom confidence and FPS
ros2 launch robot_ai ai.launch.py \
  model_path:=/path/to/yolo11n.onnx \
  confidence_threshold:=0.3 \
  fps_limit:=10.0

# Disable detection (idle mode)
ros2 launch robot_ai ai.launch.py enable_detection:=false
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_path` | string | "" | Path to .onnx or .pt model |
| `confidence_threshold` | float | 0.5 | Min detection confidence |
| `iou_threshold` | float | 0.45 | NMS threshold |
| `fps_limit` | float | 5.0 | Max inference rate |
| `camera_width` | int | 640 | Camera resolution |
| `camera_height` | int | 480 | Camera resolution |
| `enable_gpu` | bool | false | GPU acceleration |
| `enable_detection` | bool | true | Enable/disable at runtime |
| `frame_id` | string | camera_link | TF frame |

## Topics

| Topic | Type | Direction | Description |
|-------|------|-----------|-------------|
| `/camera/image_raw` | Image | Sub | Camera frames |
| `/robot/ai/detections` | DetectionArray | Pub | Detection results |
| `/robot/ai/status` | AIStatus | Pub | Performance metrics |

## Check

```bash
# View detections
ros2 topic echo /robot/ai/detections

# View status (FPS, CPU, memory)
ros2 topic echo /robot/ai/status

# Check topics
ros2 topic list
```

## Full System

```bash
# Terminal 1: Camera
ros2 launch camera_node camera.launch.py

# Terminal 2: AI
ros2 launch robot_ai ai.launch.py \
  model_path:=/home/robot/robot_ws/src/robot_ai/model/yolo11n.onnx
```

## Performance Targets (RPi4)

| Metric | Target | Notes |
|--------|--------|-------|
| RAM | < 500MB | ONNX: ~150MB, PyTorch: ~400MB |
| CPU | < 60% | At 5 FPS with 640x480 |
| FPS | 5-10 | YOLOv11n ONNX on RPi4 |
| Latency | < 200ms | Per inference |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "onnxruntime not found" | `pip3 install onnxruntime` |
| "Model file not found" | Check `model_path` parameter |
| High RAM usage | Use .onnx instead of .pt |
| Low FPS | Lower `fps_limit` or reduce resolution |
| No detections | Lower `confidence_threshold` |
| Node starts but no output | Check camera_node is publishing |
