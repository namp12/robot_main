# 🚀 QUICK START - Robot Workspace trên Ubuntu

Hướng dẫn chạy nhanh hệ thống robot trên máy tính Ubuntu.

---

## 1. Cài đặt ban đầu (Chỉ chạy 1 lần)
```bash
# Cài toàn bộ thư viện, phân quyền USB và udev rules
bash setup_ubuntu.sh
```

---

## 2. Làm việc hàng ngày

### Khởi tạo môi trường (Chạy mỗi khi mở Terminal mới):
```bash
source setup_env.sh
```

### Các lệnh điều khiển nhanh:
```bash
# 1. Build lại code
robot_build

# 2. Xem mô hình 3D trên RViz2 (Kèm thanh trượt khớp)
robot_rviz

# 3. Chạy các node phần cứng (ESP32 + RPLidar C1 + Camera)
robot_minimal

# 4. Quét tạo bản đồ (SLAM)
robot_slam

# 5. Lái robot bằng phím bấm
robot_teleop

# 6. Lưu bản đồ
robot_save_map

# 7. Dẫn đường tự động (Nav2)
robot_nav

# 8. Chạy toàn bộ hệ thống kèm giao diện RViz2
robot_full
```

---

## 3. Cổng kết nối USB (Đã cố định qua Udev Rules)
- **RPLidar C1**: `/dev/rplidar` (Baudrate: `460800`)
- **ESP32 DevKit**: `/dev/esp32` (Baudrate: `115200`)
- **USB Webcam**: `/dev/video0`

Chi tiết xem tại: [UBUNTU_GUIDE.md](UBUNTU_GUIDE.md)
