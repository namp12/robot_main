# 🐧 Hướng Dẫn Phát Triển & Vận Hành Robot Trên Máy Tính Ubuntu Native

Tài liệu này cung cấp toàn bộ hướng dẫn từ A-Z để thiết lập, build, kết nối phần cứng và vận hành hệ thống robot trên máy tính cài **Ubuntu** (Ubuntu 22.04 LTS với ROS 2 Humble hoặc Ubuntu 24.04 LTS với ROS 2 Jazzy).

---

## 📌 1. Chuẩn Bị & Cài Đặt Môi Trường (One-Click Setup)

Chỉ cần chạy một script duy nhất để cài đặt toàn bộ ROS 2 packages, thư viện Python, cấp quyền thiết bị và tạo Udev Rules:

```bash
# 1. Đi đến thư mục workspace
cd /duong/dan/toi/robot_main

# 2. Chạy script cài đặt tự động
bash setup_ubuntu.sh
```

Script `setup_ubuntu.sh` sẽ tự động thực hiện:
- Cài đặt đầy đủ các gói ROS 2: SLAM Toolbox, Nav2, Robot Localization, RViz2, Joint State Publisher GUI, CvBridge, Image Transport, v.v.
- Cài đặt các thư viện Python: `pyserial`, `ultralytics` (YOLO), `opencv-python`, `fastapi`, `uvicorn`, `websockets`, `pyttsx3`, `pygame`.
- Cấu hình Udev Rules và phân quyền nhóm `dialout`, `video`, `audio` cho user hiện tại.
- Build toàn bộ workspace với `--symlink-install`.

> [!NOTE]
> Sau khi cài đặt xong lần đầu, bạn có thể cần logout/login lại để quyền truy cập cổng USB (`dialout`, `video`) có hiệu lực hoàn toàn.

---

## ⚡ 2. Làm Việc Với Môi Trường Mỗi Lần Mở Terminal

Mỗi khi mở một Terminal mới trên Ubuntu, bạn chỉ cần gõ:

```bash
source setup_env.sh
```

Lệnh này sẽ tự động:
1. Nhận diện phiên bản ROS 2 (`humble` hoặc `jazzy`) trên máy.
2. Source workspace hiện tại.
3. Quét trạng thái phần cứng (ESP32, RPLidar, Webcam).
4. Kích hoạt các lệnh tắt tiện ích (Aliases).

### Bảng Lệnh Tắt Nhanh (Aliases):
| Lệnh tắt | Tác dụng |
| :--- | :--- |
| `robot_ws` | Nhảy nhanh về thư mục workspace |
| `robot_build` | Build toàn bộ workspace (`colcon build --symlink-install`) |
| `robot_clean` | Dọn dẹp sạch sẽ `build/`, `install/`, `log/` |
| `robot_rviz` | Mở RViz2 3D hiển thị robot & chỉnh khớp mô hình |
| `robot_minimal` | Khởi động các node phần cứng (ESP32, RPLidar, Camera, Audio) |
| `robot_full` | Chạy toàn bộ hệ thống robot kèm giao diện trực quan RViz2 |
| `robot_slam` | Bật SLAM Toolbox để quét và vẽ bản đồ 2D |
| `robot_save_map` | Lưu nhanh bản đồ hiện tại |
| `robot_nav` | Bật hệ thống dẫn đường tự hành Nav2 |
| `robot_teleop` | Bật bàn phím điều khiển robot di chuyển |
| `robot_udev` | Cập nhật / nạp lại Udev Rules cho cổng USB |

---

## 🔌 3. Kết Nối Phần Cứng & Udev Rules

Khi cắm các thiết bị qua cổng USB vào máy tính Ubuntu, Udev rules sẽ tự động tạo liên kết cố định:

```
RPLidar C1M1      ──>  /dev/rplidar  (460800 baud)
ESP32 DevKit      ──>  /dev/esp32    (115200 baud)
USB Webcam (UVC)  ──>  /dev/video0   (hoặc /dev/video2)
```

Kiểm tra nhanh kết nối phần cứng:
```bash
ls -l /dev/rplidar /dev/esp32 /dev/video*
```

Nếu muốn cài đặt lại hoặc cập nhật udev rules:
```bash
robot_udev
```

---

## 🕹️ 4. Quy Trình Vận Hành & Test Thực Tế

### Bước 4.1: Kiểm tra Mô hình 3D & TF Tree (RViz2)
Chạy lệnh sau để mở mô hình 3D robot trực tiếp trên màn hình Ubuntu:
```bash
robot_rviz
```
Bạn sẽ thấy giao diện **Joint State Publisher GUI** cho phép kéo thanh trượt để quay các khớp bánh xe, camera, LiDAR và kiểm tra TF tree hoàn chỉnh.

---

### Bước 4.2: Khởi động Hardware Stack
Bật kết nối với ESP32, RPLidar C1 và Camera:
```bash
robot_minimal
```
Các topic chính sẽ được publish:
- `/scan`: Dữ liệu quét LaserScan từ RPLidar C1
- `/camera/image_raw`: Luồng hình ảnh từ Camera
- `/wheel_encoder`, `/imu_raw`, `/battery_voltage`: Dữ liệu từ ESP32
- `/cmd_vel`: Điều khiển tốc độ bánh xe

---

### Bước 4.3: Quét Bản Đồ Môi Trường (SLAM)
Mở một terminal mới:
```bash
source setup_env.sh
robot_slam
```
Mở thêm một terminal khác để lái robot đi khắp phòng:
```bash
source setup_env.sh
robot_teleop
```
*(Sử dụng các phím `i`, `j`, `k`, `l`, `,` để điều khiển tốc độ và hướng đi)*

Sau khi quét xong toàn bộ phòng, lưu bản đồ lại bằng:
```bash
robot_save_map
# Hoặc đặt tên riêng:
bash save_map.sh src/robot_bringup/maps/my_room/map
```

---

### Bước 4.4: Dẫn Đường Tự Động (Nav2)
Sau khi có bản đồ:
```bash
source setup_env.sh
robot_nav
```
Mở RViz2, chọn công cụ **"2D Pose Estimate"** để chỉ định vị trí ban đầu của robot, sau đó chọn **"Nav2 Goal"** để chỉ định điểm đến. Robot sẽ tự động tính toán đường đi tránh vật cản và di chuyển đến đích.

---

### Bước 4.5: Chạy Nhận Diện AI (YOLO) & Tương Tác
Nhờ chạy trực tiếp trên máy tính Ubuntu (CPU/GPU mạnh mẽ), bạn có thể chạy mô hình YOLOv8/YOLO11 nhận diện vật thể với tốc độ khung hình cao:
```bash
source setup_env.sh
ros2 launch robot_bringup ai.launch.py enable_ai:=true
```

---

## 🛠️ 5. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

### 1. Không mở được cổng Serial (`Permission Denied`):
```bash
sudo usermod -aG dialout $USER
# Sau đó chạy lệnh sau để áp dụng ngay:
newgrp dialout
```

### 2. RPLidar hoặc ESP32 không nhận `/dev/rplidar` hoặc `/dev/esp32`:
Kiểm tra ID thiết bị thực tế bằng lệnh `lsusb`:
```bash
lsusb
```
Nếu mã `ID xxxx:yyyy` khác với mã mặc định, bạn có thể chỉnh sửa file [udev/99-robot-usb.rules](file:///d:/robot_main/udev/99-robot-usb.rules) và chạy lại `robot_udev`.

### 3. Camera báo lỗi `Device busy` hoặc sai index:
Kiểm tra danh sách camera có sẵn:
```bash
v4l2-ctl --list-devices
```
Chỉ định cổng camera mong muốn khi chạy:
```bash
ros2 launch camera_node camera.launch.py camera_index:=0
```

---

*Hệ thống đã sẵn sàng cho việc phát triển toàn diện trên Ubuntu PC!*
