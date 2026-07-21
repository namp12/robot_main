# QUICK START - Robot Serial

```bash
# 1. Build
cd ~/robot_ws
colcon build --packages-select robot_serial

# 2. Setup environment
source install/setup.bash

# 3. Run
ros2 launch robot_serial robot_serial.launch.py
```

## Expected Output

✓ **Node started**:
```
[INFO] [serial_node]: Serial node initialized
[INFO] [serial_node]: Connected to /dev/ttyACM0
```

✓ **Data received** (e.g., `Hello Pi`):
```
[INFO] [serial_node]: [RX]
Hello Pi
```

✓ **Device not found** (retry every 2s):
```
[ERROR] [serial_node]: Serial device not found.
```

✓ **Disconnected** (auto reconnect):
```
[WARN] [serial_node]: Serial disconnected.
[INFO] [serial_node]: Connected to /dev/ttyACM0
```

## Files Created/Modified

**Core:**
- `robot_serial/serial_node.py` - ROS2 Node
- `robot_serial/serial_manager.py` - Serial Manager Class
- `launch/robot_serial.launch.py` - Launch file
- `setup.py` - Entry points

**Documentation:**
- `USAGE.md` - Detailed usage guide
- `ROBOT_SERIAL_SETUP.md` - Complete setup guide
- `QUICK_START.md` - This file

**Testing:**
- `test_robot_serial.sh` - Comprehensive tests
- `test_robot_serial_unit.py` - Unit tests
- `test_serial_send.py` - Manual sender

## Key Features

✅ Auto port detection (USB0, USB1, ACM0, ACM1)
✅ 115200 baud, 100ms timeout
✅ Automatic reconnection
✅ No crashes, graceful handling
✅ ROS2 logger integration
✅ Clean architecture (easy to extend)

## Next Phase

Just plug in ESP32 and start sending data. The node will:
1. Find the port
2. Connect
3. Log every line received

When ready to expand:
- Add JSON parser
- Add ROS2 publishers
- Add subscribers for commands
