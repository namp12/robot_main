# Hướng dẫn kết nối ROS2 sau khi test phần cứng thành công

## Kiểm tra phần cứng đã sẵn sàng

Trước khi kết nối ROS2, đảm bảo đã test thành công:

1. **Motor test**: `pio run -e test_motor -t upload`
   - Chạy `FORWARD 180`, `BACKWARD 150`, `STOP`
   - 4 motor quay đúng chiều
   - Encoder đếm đúng

2. **Sensor test**: `pio run -e test_sensor -t upload`
   - Chạy `ALL`
   - IMU: số thay đổi khi nghiêng/xoay
   - ENCODER: đếm đúng
   - DISTANCE: thay đổi khi có vật cản
   - BATTERY: điện áp hợp lý

3. **Firmware chính**: `pio run -e esp32dev -t upload`
   - Monitor: `pio device monitor`
   - Gửi: `MODE TEST`, `MOVE FORWARD 150`, `MOVE STOP`
   - Xác nhận robot điều khiển được
   - Xác nhận telemetry gửi về đều đặn

## Sơ đồ kết nối phần cứng

Raspberry Pi 4                    ESP32
-----------                       ------
USB cable -----> /dev/ttyACM0

## Cấu hình ROS2 trên Raspberry Pi

### 1. Xác định cổng Serial

```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
```

ESP32 tự động nhận diện cổng trong firmware.

### 2. Chạy ROS2 Serial Node

```bash
cd ~/robot_ws
source install/setup.bash
ros2 launch robot_serial robot_serial.launch.py
```

Node sẽ:
- Kết nối /dev/ttyACM0
- Đọc telemetry từ ESP32
- Xuất topic: `/esp32/serial_rx`, `/imu/data`, `/sensor/front_distance`, `/sensor/rear_distance`, `/sensor/battery`

### 3. Điều khiển Text Mode

```bash
# Chuyển sang TEST mode
ros2 topic pub /esp32/serial_tx std_msgs/msg/String "{data: 'MODE TEST'}" --once

# Chạy tiến
ros2 topic pub /esp32/serial_tx std_msgs/msg/String "{data: 'MOVE FORWARD 180'}" --once

# Dừng
ros2 topic pub /esp32/serial_tx std_msgs/msg/String "{data: 'MOVE STOP'}" --once

# Chuyển về MANUAL
ros2 topic pub /esp32/serial_tx std_msgs/msg/String "{data: 'MODE MANUAL'}" --once
```

### 4. Điều khiển ROS2 Binary Mode

Nếu muốn dùng binary protocol giống `esp32_ros2_bridge`:

```bash
# Trên Raspberry Pi, chạy esp32 bridge node
ros2 run esp32_ros2_bridge esp32_bridge_node
```

Nhưng cần đảm bảo firmware ESP32 đang ở chế độ binary mode. Hiện firmware chính hỗ trợ cả 2 mode:
- TEXT: qua topic `/esp32/serial_tx`
- BINARY: qua node `esp32_bridge_node`

### 5. Xác minh topics hoạt động

```bash
# Liệt kê topics
ros2 topic list

# Lắng nghe serial rx
ros2 topic echo /esp32/serial_rx

# Lắng nghe IMU
ros2 topic echo /imu/data

# Lắng nghe distance
ros2 topic echo /sensor/front_distance
ros2 topic echo /sensor/rear_distance
```

## Troubleshooting ROS2 kết nối

1. **Permission denied /dev/ttyACM0**:
   ```bash
   sudo usermod -aG dialout $USER
   # Logout và login lại
   ```

2. **Kết nối serial fail**:
   ```bash
   # Kiểm tra cổng
   ls -la /dev/ttyACM*
   
   # Thử cổng khác
   # Có thể cần unplug và replug ESP32
   ```

3. **ESP32 nhận lệnh nhưng không chạy motor**:
   - Kiểm tra code đang ở MODE nào: xem log Serial monitor
   - Chuyển sang TEST mode: `MODE TEST`
   - Gửi lệnh text: `MOVE FORWARD 150`

4. **Telemetry không cập nhật**:
   - Kiểm tra baudrate: cả 2 bên phải 115200
   - Kiểm tra dây USB (nếu dùng USB-Serial adapter)
   - Xem Serial monitor trên PlatformIO: `pio device monitor`

## Tích hợp Nav2 (tương lai)

ESP32 firmware đã chuẩn bị cho Nav2:
- Chế độ ROS2 nhận binary frames `0xFF 0xFE`
- Topic `/cmd_vel` sẽ được map thành wheel speeds
- Cần cập nhật `robot_serial` node để convert `/cmd_vel` sang binary protocol

Hiện tại điều khiển thông qua text protocol:
```
MOVE FORWARD <speed>
MOVE ROTATE_LEFT <speed>
```

## Tích hợp Web Backend (tương lai)

Web backend (FastAPI) -> ROS2 -> robot_serial -> ESP32

- Web API gửi HTTP request
- ROS2 node convert sang command text
- `ros2 topic pub /esp32/serial_tx` gửi lệnh

Các text commands đã sẵn sàng:
- `MODE MANUAL` / `MODE AUTO` / `MODE ROS` / `MODE TEST`
- `MOVE FORWARD <speed>` ... (10 hướng)
- `SET_SAFE_DISTANCE <cm>`
- `SET_TIMEOUT <ms>`

## Checklist Triển khai

- [ ] Cấu hình pinout trong `config.h` đúng với phần cứng thực tế
- [ ] Test motor từng bánh với `test_motor`
- [ ] Test sensors với `test_sensor`
- [ ] Nạp firmware chính
- [ ] Test text commands qua Serial Monitor
- [ ] Test điều khiển qua ROS2 topic
- [ ] Verify telemetry về ROS2 đúng
- [ ] Test safety e-stop (đặt vật cản trước robot)
- [ ] Tích hợp với robot_serial launch file
- [ ] (Tùy chọn) Implement binary protocol cho Nav2

## Tối ưu sau này

1. Calibration IMU: thêm `calibrate()` method
2. PID cho encoder feedback
3. Watchdog cho cảm biến
4. Timeout cho mỗi command
5. Logging qua SD card
6. OTA update
7. Battery low voltage warning trên app/web
