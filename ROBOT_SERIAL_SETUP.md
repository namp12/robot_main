# Robot Serial - Kiểm Tra Kết Nối ESP32

## ✓ Package đã hoàn thành

Tất cả các yêu cầu đã được thực hiện:

### 1. ✓ Tự động dò cổng Serial
- Ưu tiên: `/dev/ttyUSB0` → `/dev/ttyUSB1` → `/dev/ttyACM0` → `/dev/ttyACM1`
- Nếu không tìm thấy: In `[ERROR] Serial device not found.` mỗi 2 giây
- Không crash node, tiếp tục thử lại

### 2. ✓ Kết nối Serial
- Baudrate: **115200**
- Timeout: **100ms**
- Khi kết nối: In `[INFO] Connected to /dev/ttyACM0` (hoặc port thực tế)

### 3. ✓ Đọc dữ liệu
- Đọc liên tục từng dòng
- Log: `[RX]\n<dữ liệu nhận>`
- Không parse JSON (như yêu cầu)
- Chỉ đọc nguyên dòng

### 4. ✓ Mất kết nối
- In: `[WARN] Serial disconnected.`
- Tự động reconnect
- Không thoát node

### 5. ✓ Logging
- Dùng ROS2 logger (`rclpy.get_logger()`)
- Không dùng `printf`

### 6. ✓ Launch File
- File: `launch/robot_serial.launch.py`
- Chạy: `ros2 launch robot_serial robot_serial.launch.py`

### 7. ✓ Cấu trúc Code
Dùng Python với cấu trúc rõ ràng:
```
robot_serial/
├── serial_node.py        # ROS2 Node
├── serial_manager.py     # Quản lý Serial
└── __init__.py
launch/
└── robot_serial.launch.py
```

### 8. ✓ Chất lượng Code
- Class rõ ràng: `SerialManager`, `SerialNode`
- Reconnect tự động
- Dễ mở rộng (callbacks, clean separation)
- Sau này chỉ cần thêm parser JSON & publisher ROS2

### 9. ✓ Kiểm tra
- Build: ✓ Passed
- Source: ✓ Passed
- Launch: ✓ Passed
- Unit tests: ✓ All passed

---

## 🚀 Cách sử dụng

### 1. Build package
```bash
cd ~/robot_ws
colcon build --packages-select robot_serial
source install/setup.bash
```

### 2. Khởi động node
```bash
ros2 launch robot_serial robot_serial.launch.py
```

### 3. Dự kiến output
Nếu ESP32 chưa kết nối:
```
[INFO] [serial_node]: Serial node initialized
[ERROR] [serial_node]: Serial device not found.
[ERROR] [serial_node]: Serial device not found.  # mỗi 2 giây
```

Khi ESP32 được kết nối USB:
```
[INFO] [serial_node]: Serial node initialized
[INFO] [serial_node]: Connected to /dev/ttyACM0
```

Khi ESP32 gửi `Hello Pi`:
```
[INFO] [serial_node]: [RX]
Hello Pi
```

### 4. Mất kết nối (rút USB)
```
[WARN] [serial_node]: Serial disconnected.
[INFO] [serial_node]: Connected to /dev/ttyACM0  # tự động reconnect
```

---

## 📝 Code Structure

### `SerialManager` (serial_manager.py)
- **Trách nhiệm**: Quản lý kết nối Serial
- **Tính năng**:
  - Tự động dò port
  - Kết nối với timeout
  - Đọc dữ liệu non-blocking
  - Callbacks cho connection/data/disconnection
- **Dễ mở rộng**: Có thể thêm parser hoặc publisher

### `SerialNode` (serial_node.py)
- **Trách nhiệm**: ROS2 Node
- **Tính năng**:
  - Wrapper xung quanh SerialManager
  - Tự động reconnect (timer 100ms)
  - Log với ROS2 logger
  - Graceful shutdown

---

## 🔧 Cấu hình

Nếu cần thay đổi, chỉnh sửa `serial_manager.py`:

```python
class SerialManager:
    SERIAL_PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
    BAUDRATE = 115200        # Thay đổi baudrate
    TIMEOUT_MS = 100         # Thay đổi timeout
```

---

## 🧪 Testing

Chạy comprehensive tests:
```bash
cd ~/robot_ws
bash test_robot_serial.sh
```

Chạy unit tests:
```bash
cd ~/robot_ws
python3 test_robot_serial_unit.py
```

---

## 📚 Tệp được tạo/cập nhật

- ✓ `robot_serial/serial_node.py` (mới)
- ✓ `robot_serial/serial_manager.py` (mới)
- ✓ `launch/robot_serial.launch.py` (cập nhật)
- ✓ `setup.py` (cập nhật entry point)
- ✓ `USAGE.md` (hướng dẫn chi tiết)
- ✓ `test_robot_serial.sh` (test script)
- ✓ `test_robot_serial_unit.py` (unit tests)
- ✓ `test_serial_send.py` (test sender)

---

## ✨ Lưu ý

- **Không có**: publish ROS2 topic, subscribe cmd_vel, parse JSON, điều khiển ESP32
- **Chỉ có**: kiểm tra kết nối Serial, đọc dữ liệu, log
- **Dễ mở rộng**: Sau này chỉ cần thêm JSON parser + ROS2 publisher

---

## 📞 Troubleshooting

### Node không tìm thấy serial port
```bash
# Kiểm tra port tồn tại
ls -la /dev/ttyACM0

# Kiểm tra quyền truy cập
sudo usermod -a -G dialout $USER
# Đăng xuất và đăng nhập lại

# Kiểm tra ESP32 được nhận diện
lsusb
```

### Không nhận được dữ liệu từ ESP32
```bash
# Kiểm tra baudrate
stty -F /dev/ttyACM0 115200

# Kiểm tra dữ liệu từ ESP32
cat /dev/ttyACM0
# Ctrl+C để thoát

# Kiểm tra pyserial
python3 -c "import serial; print(serial.__version__)"
```

---

## 🎯 Bước tiếp theo (Không làm lúc này)

Sau khi kiểm tra kết nối OK, có thể:
1. **Thêm JSON parser**: Phân tích dữ liệu JSON từ ESP32
2. **Thêm ROS2 publisher**: Xuất bản data lên topic
3. **Thêm ROS2 subscriber**: Nhận cmd từ các node khác
4. **Thêm cấu hình file**: Dùng YAML config thay vì hardcode

---

**Status**: ✅ **HOÀN THÀNH** - Sẵn sàng kiểm tra kết nối ESP32
