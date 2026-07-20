# Autonomous Delivery Robot - ROS2 Humble

Hệ thống robot giao hàng tự hành sử dụng ROS2 Humble trên Raspberry Pi 4.

## Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4 (4GB)                         │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │ camera_node   │   │ sllidar_ros2 │   │ robot_serial     │    │
│  │ (Webcam)      │   │ (RPLidar C1) │   │ (ESP32 Bridge)   │    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────────┘    │
│         │                   │                   │                │
│         │ /camera/image_raw │ /scan             │ /wheel_encoder │
│         │                   │                   │ /imu_raw       │
│         │                   │                   │ /battery_voltage│
│         │                   │                   │ /cmd_vel       │
│  ┌──────┴───────────────────┴───────────────────┴───────────┐   │
│  │                    ROS2 Topics                            │   │
│  └──────┬───────────────────┬───────────────────┬───────────┘   │
│         │                   │                   │                │
│  ┌──────┴───────┐   ┌──────┴───────┐   ┌──────┴───────────┐    │
│  │vision_ai_node│   │slam_toolbox  │   │ robot_description│    │
│  │ (YOLO AI)    │   │ (SLAM)       │   │ (Robot Model)    │    │
│  └──────────────┘   └──────────────┘   └──────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              robot_bringup (Master Launch)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                              │
    USB Webcam                    USB Serial
    RPLidar C1                    ESP32 DevKit
```

## Môi trường

| Thành phần | Chi tiết |
|-------------|----------|
| SBC | Raspberry Pi 4 (4GB RAM) |
| OS | Ubuntu Server 22.04 |
| ROS2 | Humble |
| Lidar | RPLidar C1M1 (12m, 360°) |
| Camera | UGREEN USB Webcam (UVC) |
| MCU | ESP32 DevKit V1 (UART qua USB) |
| Workspace | `~/robot_ws` |

## Packages

| # | Package | Loại | Mô tả |
|---|---------|------|--------|
| 1 | `robot_description` | CMake | Mô hình URDF/xacro robot (13 links, TF tree) |
| 2 | `robot_bringup` | CMake | Master launch files (lidar, SLAM, localization) |
| 3 | `camera_node` | Python | Driver webcam USB - publish `/camera/image_raw` |
| 4 | `vision_ai_node` | Python | YOLO object detection - subscribe camera, publish detections |
| 5 | `vision_msgs` | CMake | Custom message definitions (Detection, DetectionArray) |
| 6 | `robot_serial` | Python | Serial bridge ESP32 - encoder, IMU, battery, cmd_vel |
| 7 | `sllidar_ros2` | CMake | Driver RPLidar C1M1 - publish `/scan` |

## Cài đặt Dependencies

```bash
# ROS2 core
sudo apt install ros-humble-desktop

# Lidar
sudo apt install ros-humble-sllidar-ros2

# SLAM
sudo apt install ros-humble-slam-toolbox

# Camera & Vision
sudo apt install ros-humble-cv-bridge ros-humble-sensor-msgs python3-opencv

# Serial
pip3 install pyserial

# YOLO (cho vision_ai_node)
pip3 install ultralytics
```

## Build toàn bộ workspace

```bash
cd ~/robot_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

Build từng package:

```bash
colcon build --packages-select robot_description
colcon build --packages-select robot_bringup
colcon build --packages-select camera_node
colcon build --packages-select vision_msgs
colcon build --packages-select vision_ai_node
colcon build --packages-select robot_serial
```

---

## Cách chạy từng Node

### 1. Robot Description (Robot Model + TF)

Khởi tạo robot model và publish TF tree.

```bash
# Xem robot trong RViz (trên laptop có GUI)
ros2 launch robot_description display.launch.py

# Chỉ chạy robot_state_publisher (cho RPi, không GUI)
ros2 launch robot_description robot_state_publisher.launch.py
```

| Topic | Type | Mô tả |
|-------|------|--------|
| `robot_description` | String | URDF XML |
| `/tf`, `/tf_static` | TFMessage | Transform tree |

---

### 2. RPLidar C1M1 (Lidar)

Khởi động lidar, publish scan data.

```bash
# Qua bringup launch
ros2 launch robot_bringup lidar.launch.py

# Hoặc trực tiếp từ sllidar_ros2
ros2 launch sllidar_ros2 sllidar_c1_launch.py
```

| Topic | Type | Mô tả |
|-------|------|--------|
| `/scan` | LaserScan | Điểm mây 360° (12m range) |

**Tham số:**

```bash
ros2 launch robot_bringup lidar.launch.py serial_port:=/dev/ttyUSB0
```

---

### 3. Camera Node (Webcam Driver)

Đọc webcam UGREEN, publish hình ảnh.

```bash
# Mặc định (640x480 @ 15 FPS)
ros2 launch camera_node camera.launch.py

# Tùy chỉnh
ros2 launch camera_node camera.launch.py width:=1280 height:=720 fps:=30.0
```

| Topic | Type | Mô tả |
|-------|------|--------|
| `/camera/image_raw` | Image | Frame ảnh BGR |
| `/camera/camera_info` | CameraInfo | Thông tin camera |

**Kiểm tra:**

```bash
ros2 topic echo /camera/image_raw --once
ros2 run rqt_image_view rqt_image_view
```

---

### 4. Vision AI Node (YOLO Detection)

Nhận ảnh từ camera, chạy YOLO, publish kết quả.

```bash
# Idle (không chạy AI)
ros2 launch vision_ai_node vision_ai.launch.py

# Bật YOLO với model
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/path/to/yolov8n.pt

# Tùy chỉnh confidence và FPS
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/path/to/yolov8n.pt \
  confidence_threshold:=0.3 \
  max_fps:=3.0
```

| Topic | Type | Hướng | Mô tả |
|-------|------|-------|--------|
| `/camera/image_raw` | Image | Sub | Ảnh từ camera |
| `/vision/detections` | DetectionArray | Pub | Kết quả YOLO |
| `/vision/annotated_image` | Image | Pub | Ảnh có bounding box |
| `/vision/status` | String | Pub | Trạng thái node |

---

### 5. Robot Serial (ESP32 Bridge)

Cầu nối serial giữa Raspberry Pi và ESP32.

```bash
# Mặc định (/dev/ttyACM0, 115200)
ros2 launch robot_serial robot_serial.launch.py

# Tùy chỉnh port
ros2 launch robot_serial robot_serial.launch.py port:=/dev/ttyUSB0 baudrate:=9600
```

| Topic | Type | Hướng | Mô tả |
|-------|------|-------|--------|
| `/wheel_encoder` | Int32MultiArray | Pub | Encoder trái/phải |
| `/imu_raw` | Imu | Pub | Gia tốc IMU |
| `/battery_voltage` | Float32 | Pub | Điện áp pin |
| `/wheel_rpm` | Int32MultiArray | Pub | RPM bánh xe |
| `/robot_status` | String | Pub | Trạng thái robot |
| `/cmd_vel` | Twist | Sub | Lệnh tốc độ → ESP32 |

**Gửi lệnh tốc độ:**

```bash
# Tiến 0.25 m/s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.25}, angular: {z: 0.0}}"

# Dừng
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

---

### 6. SLAM (Lập bản đồ)

Quét bản đồ phòng bằng SLAM Toolbox.

```bash
# Chạy lidar + SLAM together
ros2 launch robot_bringup slam.launch.py

# Hoặc đầy đủ: lidar + SLAM + robot model
ros2 launch robot_bringup robot.launch.py
```

| Topic | Type | Mô tả |
|-------|------|--------|
| `/map` | OccupancyGrid | Bản đồ 2D |
| `/scan` | LaserScan | Input cho SLAM |

**Xem bản đồ trong RViz:**

```bash
ros2 launch robot_bringup view_robot.launch.py
```

---

### 7. Localization (Định vị trên bản đồ có sẵn)

Nạp bản đồ đã lưu và định vị robot.

```bash
ros2 launch robot_bringup localization.launch.py \
  map:=/mnt/robot_hdd/maps/my_room/map.yaml
```

---

## Chạy Full System (Tất cả nodes)

### Terminal 1 - Robot Core (RPi)

```bash
source /opt/ros/humble/setup.bash
source ~/robot_ws/install/setup.bash

# Robot model + Lidar + SLAM
ros2 launch robot_bringup robot.launch.py
```

### Terminal 2 - Camera (RPi)

```bash
ros2 launch camera_node camera.launch.py
```

### Terminal 3 - Serial ESP32 (RPi)

```bash
ros2 launch robot_serial robot_serial.launch.py
```

### Terminal 4 - Vision AI (RPi, optional)

```bash
ros2 launch vision_ai_node vision_ai.launch.py \
  enable_detection:=true \
  model_path:=/home/robot/models/yolov8n.pt
```

### Terminal 5 - RViz (Laptop, optional)

```bash
ros2 launch robot_bringup view_robot.launch.py
```

---

## Lưu bản đồ

```bash
# Lưu vào HDD rời
ros2 run robot_bringup save_map.sh my_room

# Hoặc tự động mount HDD rồi lưu
ros2 run robot_bringup save_map.sh my_room --auto
```

## Cấu trúc thư mục workspace

```
~/robot_ws/
├── src/
│   ├── robot_description/     # URDF/xacro robot model
│   ├── robot_bringup/         # Master launch + SLAM config
│   ├── camera_node/           # Webcam driver
│   ├── vision_ai_node/        # YOLO AI detection
│   ├── vision_msgs/           # Custom messages
│   ├── robot_serial/          # ESP32 serial bridge
│   └── sllidar_ros2/          # RPLidar C1 driver
├── build/
├── install/
└── log/
```

## TF Tree

```
map
 └── odom
      └── base_footprint
           └── base_link
                ├── left_wheel
                ├── right_wheel
                ├── rear_caster_wheel
                ├── laser              (RPLidar C1)
                ├── camera_link        (Webcam)
                │    └── camera_optical_frame
                ├── imu_link
                ├── raspberry_pi
                └── battery
```

## Serial Protocol (ESP32 ↔ Pi)

**ESP32 → Pi:**

| Format | Ví dụ | Mô tả |
|--------|--------|--------|
| `<ENC,L,R>` | `<ENC,120,118>` | Encoder ticks |
| `<IMU,ax,ay,az>` | `<IMU,0.02,-0.01,9.81>` | Gia tốc (m/s²) |
| `<BAT,V>` | `<BAT,15.63>` | Điện áp pin |
| `<RPM,L,R>` | `<RPM,120,121>` | Vòng/phút bánh xe |
| `<STATUS,OK>` | `<STATUS,OK>` | Trạng thái |

**Pi → ESP32:**

| Format | Ví dụ | Mô tả |
|--------|--------|--------|
| `<CMD,lin,ang>` | `<CMD,0.25,0.00>` | Lệnh tốc độ |
| `<PID,Kp,Ki,Kd>` | `<PID,1.00,0.10,0.01>` | Tuning PID |
| `<LED,0\|1>` | `<LED,1>` | Bật/tắt LED |
| `<STOP>` | `<STOP>` | Dừng khẩn cấp |
| `<RESET>` | `<RESET>` | Reset ESP32 |

## Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|------|-------------|-----------|
| `Cannot open camera` | Webcam chưa cắm | Kiểm tra `ls /dev/video*` |
| `Permission denied` serial | Thiếu quyền | `sudo usermod -aG dialout $USER` |
| `No such file or directory` serial | ESP32 chưa kết nối | Kiểm tra `ls /dev/ttyACM*` |
| Lidar không quay | Sai port | Kiểm tra `serial_port` trong launch |
| `ultralytics not found` | Chưa cài YOLO | `pip3 install ultralytics` |
| TF tree bị đứt | Thiếu robot_state_publisher | Chạy `robot_state_publisher.launch.py` |
| Bản đồ không load | Sai đường dẫn | Kiểm tra `map:=` trong localization |

## License

Apache-2.0
# robot_main
# robot_main
