# Robot Serial - Serial Connection Node

ROS2 node for establishing and monitoring serial connection with ESP32.

## Features

- **Automatic Port Detection**: Searches for ESP32 on `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyACM0`, `/dev/ttyACM1` in priority order
- **Robust Connection Management**: Automatically reconnects if connection is lost
- **Real-time Data Logging**: Logs all received data with ROS2 logger
- **Non-blocking Design**: Doesn't crash if serial port is unavailable, retries every 2 seconds
- **Clean Architecture**: Separates concerns with `SerialManager` class for easy extension

## Installation

### Prerequisites

```bash
sudo apt-get install python3-serial
```

### Build

```bash
cd ~/robot_ws
colcon build --packages-select robot_serial
source install/setup.bash
```

## Usage

### Launch the node

```bash
ros2 launch robot_serial robot_serial.launch.py
```

### Expected Output When Connected

```
[INFO] [serial_node]: Serial node initialized
[INFO] [serial_node]: Connected to /dev/ttyACM0
```

### Expected Output When No Device Found

```
[INFO] [serial_node]: Serial node initialized
[ERROR] [serial_node]: Serial device not found.
[ERROR] [serial_node]: Serial device not found.  # repeats every 2 seconds
```

When device is plugged in, node automatically connects:

```
[INFO] [serial_node]: Connected to /dev/ttyACM0
```

### Receiving Data

When ESP32 sends data, the node logs:

```
[INFO] [serial_node]: [RX]
Hello Pi
```

Multiple lines:
```
[INFO] [serial_node]: [RX]
{"battery": 12.4}
[INFO] [serial_node]: [RX]
Status: OK
```

### Disconnection Handling

If ESP32 is unplugged:

```
[WARN] [serial_node]: Serial disconnected.
```

Node automatically searches for device again and reconnects when plugged back in.

## Testing

### Manual Test with Serial Monitor

1. Start the node:
```bash
ros2 launch robot_serial robot_serial.launch.py
```

2. Send data from another terminal using screen or minicom:
```bash
# Install (if needed)
sudo apt-get install minicom

# Open serial connection
minicom -D /dev/ttyACM0 -b 115200

# Type messages and press Enter
```

### Automated Test (requires two virtual serial ports)

Use `socat` to create virtual serial port pair for testing:

```bash
# Terminal 1: Create virtual port pair
socat -d -d PTY,raw,echo=0 PTY,raw,echo=0

# Note the two ports created (e.g., /dev/pts/10 and /dev/pts/11)

# Terminal 2: Start ROS2 node (pointing to virtual port)
# Edit SerialManager to use the first virtual port

# Terminal 3: Send test data to the other virtual port
python3 src/robot_serial/test_serial_send.py --port /dev/pts/11
```

## Code Structure

### SerialManager (`robot_serial/serial_manager.py`)

- Handles serial port detection and connection
- Manages read operations with proper exception handling
- Provides callbacks for connection/disconnection/data events
- Designed for easy extension with JSON parser or publishers

**Key Methods:**
- `find_serial_port()`: Auto-detect available port
- `connect()`: Establish serial connection
- `read_line()`: Non-blocking read
- `disconnect()`: Clean up serial port

### SerialNode (`robot_serial/serial_node.py`)

- ROS2 Node wrapper around SerialManager
- Uses timer callback for periodic tasks
- Logs data using ROS2 logger
- Implements automatic reconnection logic

## Configuration

Current configuration is hardcoded in `SerialManager`:
- **Baudrate**: 115200
- **Timeout**: 100ms
- **Retry Interval**: 2 seconds (logging)
- **Ports to Check**: `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyACM0`, `/dev/ttyACM1`

To modify, edit `robot_serial/serial_manager.py`:

```python
BAUDRATE = 115200  # Change baudrate
TIMEOUT_MS = 100   # Change timeout
SERIAL_PORTS = [...]  # Add/remove ports
```

## Future Extensions

This architecture is designed for easy extension:

1. **Add JSON parsing**: Create `JsonParser` class that accepts raw data, parses JSON
2. **Add ROS2 publishers**: Create publishers for specific message types
3. **Add command subscriptions**: Subscribe to cmd_vel or other topics
4. **Add configuration file**: Move hardcoded values to YAML config
5. **Add data validation**: Add checksums or validation layer

## Troubleshooting

### Node won't find serial port

1. Check port exists:
```bash
ls -la /dev/ttyACM0  # or your port
```

2. Check permissions:
```bash
# If permission denied, add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and log back in
```

3. Verify ESP32 is connected:
```bash
lsusb
# Should see "Silicon Labs CP2102" or similar
```

### Can't read data

1. Verify baudrate (default 115200):
```bash
stty -F /dev/ttyACM0 115200
```

2. Check data format (should be UTF-8, one message per line):
```bash
cat /dev/ttyACM0
# Should show ESP32 output
# Press Ctrl+C to stop
```

3. Verify pyserial is installed:
```bash
python3 -c "import serial; print(serial.__version__)"
```

## License

Apache-2.0
