# robot_serial

Serial bridge between ESP32 and ROS2 topics via USB CDC Serial.

## Architecture

```
ESP32 --[USB Serial]--> robot_serial --> ROS2 Topics
ROS2 Topics --> robot_serial --[USB Serial]--> ESP32
```

## Serial Protocol

### ESP32 -> Raspberry Pi (sensor data)

| Format | Example | Description |
|--------|---------|-------------|
| `<ENC,left,right>` | `<ENC,120,118>` | Wheel encoder ticks |
| `<IMU,ax,ay,az>` | `<IMU,0.02,-0.01,9.81>` | IMU acceleration (m/s^2) |
| `<BAT,voltage>` | `<BAT,15.63>` | Battery voltage |
| `<RPM,left,right>` | `<RPM,120,121>` | Wheel RPM |
| `<STATUS,text>` | `<STATUS,OK>` | Robot status |

### Raspberry Pi -> ESP32 (commands)

| Format | Example | Description |
|--------|---------|-------------|
| `<CMD,linear,angular>` | `<CMD,0.25,0.00>` | Velocity command |
| `<PID,Kp,Ki,Kd>` | `<PID,1.00,0.10,0.01>` | PID tuning |
| `<LED,state>` | `<LED,1>` | LED control |
| `<STOP>` | `<STOP>` | Emergency stop |
| `<RESET>` | `<RESET>` | Reset ESP32 |

## Dependencies

```bash
# Install pyserial
pip3 install pyserial

# Or via apt
sudo apt install python3-serial
```

## Build

```bash
cd ~/robot_ws
colcon build --packages-select robot_serial
source install/setup.bash
```

## Run

```bash
# Default (/dev/ttyACM0, 115200 baud)
ros2 launch robot_serial robot_serial.launch.py

# Custom port
ros2 launch robot_serial robot_serial.launch.py port:=/dev/ttyUSB0

# Custom baudrate
ros2 launch robot_serial robot_serial.launch.py baudrate:=9600

# Run node directly
ros2 run robot_serial robot_serial_node
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | string | /dev/ttyACM0 | Serial port path |
| `baudrate` | int | 115200 | Serial baud rate |
| `timeout` | float | 0.1 | Read timeout (seconds) |
| `reconnect_interval` | float | 3.0 | Reconnect interval (seconds) |
| `frame_id` | string | base_link | TF frame for IMU |

## Check Serial Connection

```bash
# List serial devices
ls -la /dev/ttyACM*

# Monitor serial output (install screen if needed)
screen /dev/ttyACM0 115200
# Press Ctrl+A then D to detach
```

## Check Topics

```bash
# List topics
ros2 topic list

# View encoder data
ros2 topic echo /wheel_encoder

# View IMU data
ros2 topic echo /imu_raw

# View battery voltage
ros2 topic echo /battery_voltage

# View robot status
ros2 topic echo /robot_status
```

## Send Velocity Commands

```bash
# Publish cmd_vel (move forward at 0.25 m/s)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.25}, angular: {z: 0.0}}"

# Stop
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

## Example ESP32 Data

```
<ENC,120,118>
<IMU,0.02,-0.01,9.81>
<BAT,15.63>
<RPM,120,121>
<STATUS,OK>
<ENC,125,123>
<IMU,0.01,-0.02,9.80>
<BAT,15.62>
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Permission denied" | `sudo usermod -aG dialout $USER` then logout/login |
| "No such file or directory" | Check `ls /dev/ttyACM*` |
| "Device busy" | Close other serial monitors (screen, Arduino IDE) |
| No data received | Check ESP32 is sending data, verify baudrate |
| Auto-reconnect failing | Check USB cable, try different USB port |

## ESP32 Arduino Example

```cpp
#include <Arduino.h>

void setup() {
  Serial.begin(115200);  // Must match robot_serial baudrate
}

void loop() {
  // Send encoder data
  Serial.print("<ENC,");
  Serial.print(leftEncoder);
  Serial.print(",");
  Serial.print(rightEncoder);
  Serial.println(">");

  // Send IMU data
  Serial.print("<IMU,");
  Serial.print(ax, 2);
  Serial.print(",");
  Serial.print(ay, 2);
  Serial.print(",");
  Serial.println(az, 2);
  Serial.println(">");

  // Send battery voltage
  Serial.print("<BAT,");
  Serial.print(batteryVoltage, 2);
  Serial.println(">");

  // Read commands from Pi
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    // Parse <CMD,linear,angular> etc.
  }

  delay(20);  // 50Hz
}
```
