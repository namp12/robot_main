# ESP32 Robot Firmware

ESP32 Robot Firmware cho hệ thống robot ROS2 Humble.

## Cấu trúc dự án

```
firmware/
  platformio.ini      # Cấu hình PlatformIO
  src/
    config.h          # Cấu hình chung, pinout, constants
    SerialProtocol.cpp/.h       # Protocol encode/decode
    MotorDriver.cpp/.h          # Điều khiển 1 motor BTS7960
    MecanumKinematics.cpp/.h    # Tính toán mecanum kinematics
    MotionController.cpp/.h     # Điều khiển 4 motor, 10 chế độ chuyển động
    EncoderManager.cpp/.h       # Đọc 4 encoder (interrupt)
    IMUManager.cpp/.h           # Đọc IMU MPU6050 qua I2C
    DistanceManager.cpp/.h      # Đọc 2 cảm biến siêu âm HC-SR04
    BatteryManager.cpp/.h       # Đọc điện áp pin qua ADC
    SensorManager.cpp/.h        # Tổng hợp tất cả sensors, build telemetry string
    SafetyController.cpp/.h     # Giám sát safety, e-stop, obstacle
    ModeManager.cpp/.h          # Quản lý mode MANUAL/AUTO/ROS2/TEST
    CommandParser.cpp/.h        # Parse text commands từ Serial
    CommandExecutor.cpp/.h      # Execute parsed commands
    ROS2Interface.cpp/.h        # Binary protocol ROS2 (0xFF 0xFE ... 0xFD)
    main.cpp                    # Firmware chính

    test_motor/
      test_motor.cpp            # Firmware test motor
    test_sensor/
      test_sensor.cpp           # Firmware test sensors
```

## Nạp code

### Setup PlatformIO
```bash
cd firmware
pio run
```

### Nạp firmware chính
```bash
cd firmware
pio run -e esp32dev -t upload
```

### Nạp test motor
```bash
cd firmware
pio run -e test_motor -t upload
```

### Nạp test sensor
```bash
cd firmware
pio run -e test_sensor -t upload
```

## Test từng bước

### Bước 1: Test Motor
```bash
cd firmware
pio run -e test_motor -t upload
pio device monitor
```

Lệnh test:
```
FORWARD 150
BACKWARD 150
STRAFE_LEFT 150
ROTATE_LEFT 150
STOP
ENCODER
```

Kiểm tra:
- Chiều quay 4 motor đúng
- Encoder tăng/giảm đúng chiều

### Bước 2: Test Sensor
```bash
cd firmware
pio run -e test_sensor -t upload
pio device monitor
```

Lệnh test:
```
IMU
ENCODER
DISTANCE
BATTERY
ALL
```

Kiểm tra:
- IMU thay đổi khi nghiêng/xoay
- Encoder đếm đúng
- Distance thay đổi khi có vật cản
- Battery đọc đúng điện áp

### Bước 3: Test Firmware chính
```bash
cd firmware
pio run -e esp32dev -t upload
pio device monitor
```

Gửi lệnh text:
```
MODE TEST
MOVE FORWARD 150
MOVE STOP
MODE MANUAL
```

Test ROS2 binary mode:
```bash
# Trên Raspberry Pi
ros2 launch robot_serial robot_serial.launch.py
```

ESP32 sẽ nhận frame binary 0xFF 0xFE từ ROS2 bridge.

### Bước 4: Test Safety
- Đặt vật cản trước/b sau robot
- ESP32 phải tự động STOP

### Bước 5: Kết nối ROS2

Cấu hình robot_serial node gửi lệnh text mode:
```bash
ros2 topic pub /esp32/serial_tx std_msgs/msg/String "data: 'MODE TEST'" --once
ros2 topic pub /esp32/serial_tx std_msgs/msg/String "data: 'MOVE FORWARD 180'" --once
```

## Lưu ý

- Tùy chỉnh pinout trong `config.h` theo phần cứng thực tế
- PID encoder chưa triển khai hoàn toàn, chỉ đếm pulse
- ROS2 binary protocol đã có parser/parser, cần match với firmware ROS2 bridge
