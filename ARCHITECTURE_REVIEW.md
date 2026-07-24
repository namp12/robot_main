# Robot Architecture Review for Mapping and Navigation

## Executive summary

The current stack is already capable of basic sensing and SLAM, but it is not yet production-ready for reliable Nav2 navigation. The biggest risks are:

1. Odometry is not yet suitable for a real Mecanum robot.
2. The current wheel odometry node in [src/robot_serial/robot_serial/wheel_odom_node.py](src/robot_serial/robot_serial/wheel_odom_node.py) is differential-drive based and will produce poor motion estimates during sideways and diagonal motion.
3. The TF tree is not yet fully aligned with Nav2 expectations.
4. The robot should use fused odometry from encoders + IMU through robot_localization.
5. SLAM Toolbox should be tuned for small indoor mapping, low-speed motion, and a LiDAR that is mounted correctly.

---

## 1) Critical subsystem review

### 1.1 ESP32 firmware

Current state:
- The ESP32 bridge in [src/robot_serial/robot_serial/serial_node.py](src/robot_serial/robot_serial/serial_node.py) publishes IMU and distance data to ROS 2.

Weaknesses:
- The firmware must publish wheel encoder counts or wheel velocities with a stable timestamp.
- The packet format should be deterministic and include sequence numbers.
- IMU data should be calibrated and published at a consistent rate.
- Encoder counts should be sampled at a fixed rate and not be delayed by motor control loops.

Recommended fixes:
- Publish a compact binary or line-based frame with:
  - timestamp_ms
  - left_encoder_count
  - right_encoder_count
  - front_distance_mm
  - rear_distance_mm
  - imu_ax, imu_ay, imu_az, imu_gx, imu_gy, imu_gz
  - battery_mv
  - crc/checksum
- Add a watchdog and heartbeat so the Pi can detect firmware stalls.

Why it matters:
- Poor firmware timing causes bad odometry and bad SLAM convergence.

How to test:
- Run the robot at low speed and inspect the serial stream for dropped packets or irregular timestamps.

How to fix:
- Increase the firmware update rate, use fixed-size frames, and add checksum validation.

---

### 1.2 Motor control and PID

Weaknesses:
- The existing architecture does not show a proper closed-loop velocity controller for each motor.
- A Mecanum robot requires independent wheel speed control; open-loop PWM alone will not be accurate.

Recommended fixes:
- Implement PID per motor channel using measured encoder velocity.
- Use velocity control rather than raw PWM command.
- Add saturation limits and anti-windup.

Why it matters:
- Poor motor control makes odometry and SLAM unstable.

How to test:
- Command a constant speed and verify the encoder feedback follows the target closely.

How to fix:
- Tune PID gains from slow speed to full speed and add feed-forward terms if needed.

---

### 1.3 Encoder reading

Weaknesses:
- The current odometry node assumes a differential-drive model and uses only left/right wheel RPM.

Recommended fixes:
- Use four wheel encoders or at least wheel-speed estimation from the four motor channels.
- Measure wheel velocity in radians/sec and publish it with timestamps.
- Use high-resolution encoders.

Why it matters:
- Mecanum motion is not well represented by a simple left/right wheel model.

How to test:
- Drive sideways and diagonally and compare the odometry path with the real path.

How to fix:
- Replace the current differential odometry logic with true Mecanum kinematics.

---

### 1.4 Encoder resolution

Recommended values:
- Use at least 1000 PPR (counts per revolution) or better.
- Prefer 2048 PPR or higher for better odometry quality.

Why it matters:
- Low resolution causes quantization noise and poor low-speed estimation.

How to test:
- Rotate the wheel slowly and see whether the encoder count changes smoothly.

How to fix:
- Upgrade the encoder hardware or use a higher-resolution sensor.

---

### 1.5 Wheel radius and wheel separation

Current state:
- The current parameters are in [src/robot_bringup/launch/minimal.launch.py](src/robot_bringup/launch/minimal.launch.py) and [src/robot_serial/robot_serial/wheel_odom_node.py](src/robot_serial/robot_serial/wheel_odom_node.py).

Recommended values:
- Measure the real wheel radius physically and use the actual value.
- Measure the actual wheel separation between wheel contact points, not the chassis centerline only.

Why it matters:
- Small errors in geometry will create systematic odometry drift.

How to test:
- Drive a known straight distance and compare the measured odometry distance to the real distance.

How to fix:
- Calibrate the radius and wheel separation by measuring real motion.

---

### 1.6 Mecanum kinematics

Critical issue:
- The current code is not Mecanum-aware. It uses a simple differential-drive equation.

Recommended implementation:
- Use the standard Mecanum inverse kinematics:
  - $v_x = \frac{1}{4}(v_{fl}+v_{fr}+v_{bl}+v_{br})$
  - $v_y = \frac{1}{4}(-v_{fl}+v_{fr}+v_{bl}-v_{br})$
  - $\omega = \frac{1}{4}(-v_{fl}+v_{fr}-v_{bl}+v_{br}) \times \frac{1}{L_x+L_y}$
- Use wheel speeds in m/s to compute body twist.

Why it matters:
- Without proper kinematics, sideways and diagonal motion corrupts localization.

How to test:
- Command forward, backward, left, right, diagonal, and rotation motion and inspect odometry quality.

How to fix:
- Replace the differential model with a proper four-wheel Mecanum model.

---

### 1.7 Odometry calculation

Current state:
- The current node publishes odometry from wheel RPM only.

Recommended approach:
- Publish raw wheel velocities from the ESP32 or Pi.
- Fuse wheel odometry + IMU with robot_localization EKF.
- Use the filtered output as the source for SLAM and Nav2.

Why it matters:
- Encoder-only odometry is insufficient for a real robot, especially when rotating and slipping.

How to test:
- Run the robot on slippery surfaces or during quick turns and inspect drift.

How to fix:
- Add IMU fusion and use a proper EKF.

---

### 1.8 Serial protocol

Weaknesses:
- The current parser in [src/robot_serial/robot_serial/sensor_parser.py](src/robot_serial/robot_serial/sensor_parser.py) is likely fragile for production use.

Recommended fixes:
- Use a versioned protocol.
- Add timestamps, packet IDs, and robust parsing.
- Keep message size small and deterministic.

Why it matters:
- Packet corruption causes bad sensor updates and unstable odometry.

How to test:
- Inject noise or disconnect/reconnect the serial link and verify the node degrades gracefully.

How to fix:
- Add checksum validation and safe parsing.

---

### 1.9 ROS 2 topics

Required topics for this architecture:
- /scan
- /tf
- /tf_static
- /odom
- /joint_states
- /imu/data

Current status from the workspace:
- /scan: present through the LiDAR node.
- /tf and /tf_static: present through robot_state_publisher.
- /odom: present from the current wheel odometry node.
- /imu/data: present from the serial bridge.
- /joint_states: not yet properly published for the real robot.

Recommended topic architecture:
- /scan: LiDAR scans
- /imu/data: IMU messages
- /odometry/raw: raw wheel odometry
- /odometry/filtered: EKF output
- /tf and /tf_static: transforms
- /joint_states: real wheel joint states
- /cmd_vel: navigation and teleop command velocity

Why it matters:
- Clear topic ownership reduces confusion and improves scalability.

How to test:
- Use `ros2 topic list` and `ros2 topic hz` to confirm rates and topics.

How to fix:
- Add the missing publishers and standardize the naming.

---

### 1.10 TF tree

Recommended tree:

- map
  - odom
    - base_link
      - laser
      - camera_link
      - imu_link

If you want Nav2 compatibility, you may also include:
- base_link -> base_footprint

Why it matters:
- For Nav2 and SLAM, the transform chain must be consistent and continuous.

How to test:
- Run `ros2 run tf2_tools view_frames` and inspect the tree.

How to fix:
- Ensure the odometry node publishes `odom -> base_link`, not a mismatched frame.

---

### 1.11 Frame IDs

Recommended frame IDs:
- `laser` for the LiDAR frame
- `camera_link` for the camera body
- `camera_optical_frame` for the optical frame
- `imu_link` for the IMU frame
- `base_link` for the robot body frame
- `odom` for the odometry frame
- `map` for the SLAM frame

Why it matters:
- Incorrect frame IDs destroy scan matching and localization.

How to test:
- Inspect the header.frame_id of `/scan`, `/imu/data`, and `/odom`.

How to fix:
- Keep frame IDs consistent in the drivers, URDF, and launch files.

---

### 1.12 Timestamp synchronization

Weaknesses:
- The serial bridge and wheel odometry may not be synchronized tightly enough with the IMU and LiDAR timestamps.

Recommended fixes:
- Use `rclcpp::Clock` or ROS 2 time consistently.
- Keep all sensors on the same system time or use a NTP-synced host.
- Stamp messages immediately when they are read.

Why it matters:
- Bad timestamps break sensor fusion and localization.

How to test:
- Check `/clock` and inspect timestamp differences between IMU, odometry, and LiDAR.

How to fix:
- Use NTP and ensure each driver stamps with the same ROS clock source.

---

### 1.13 IMU integration and calibration

Recommended fixes:
- Calibrate the accelerometer and gyroscope offsets.
- Publish IMU in the correct frame, ideally `imu_link`.
- Fuse IMU with wheel odometry using robot_localization.

Why it matters:
- The IMU helps during rotations and low-velocity motion where wheel odometry is weak.

How to test:
- Rotate the robot and inspect the IMU angular velocity stability.

How to fix:
- Apply calibration offsets and use a proper EKF.

---

### 1.14 LiDAR mounting position and scan quality

Recommended setup:
- Mount the LiDAR at a height of roughly 20-30 cm above the chassis top to reduce ground reflections.
- Keep it level or at a slight tilt for better indoor scan quality.
- Avoid mounting it too close to the chassis or near metal surfaces.

Recommended checks:
- Scan frequency: 10-15 Hz is a good starting point.
- Mounting angle: 0 to 5 degrees is usually fine.
- Blind spots: avoid placing the LiDAR near the wheel wells or chassis edges.

Why it matters:
- Bad scan geometry lowers map quality and causes SLAM drift.

How to test:
- Visually inspect the map for ghost walls, duplicate features, or missing corridor geometry.

How to fix:
- Adjust the mounting height and angle and remove reflective or occluding objects.

---

### 1.15 Camera node

Recommended practices:
- Publish the camera stream on a clear topic such as `/camera/image_raw`.
- Use a proper optical frame, `camera_optical_frame`.
- Keep the camera timestamped and synchronized.

Why it matters:
- The camera is important for AI and future person-following, but it does not directly improve SLAM unless used with a visual odometry or object perception pipeline.

How to test:
- Verify the image stream and frame rate with `rqt_image_view` or `ros2 topic hz`.

How to fix:
- Ensure camera calibration and correct optical frame configuration.

---

### 1.16 robot_state_publisher, URDF, and joints

Current state:
- The URDF in [src/robot_description/urdf/robot.urdf.xacro](src/robot_description/urdf/robot.urdf.xacro) is a useful starting point, but it models a differential-drive style robot rather than a Mecanum kinematic robot.

Recommended fixes:
- Replace the wheel-only model with a true Mecanum-wheel description or at least a clear placeholder until the real kinematics is implemented.
- Use `base_link` as the primary body frame and `base_footprint` as the projection frame if needed.
- Publish `/joint_states` from the actual wheel encoder state.

Why it matters:
- A wrong URDF makes the TF tree and visualization misleading.

How to test:
- Visualize the robot in RViz and verify the wheel and sensor frames match the physical robot.

How to fix:
- Update the URDF and publish the correct joint states.

---

## 2) Topic and TF verification

### Required topics

The robot should publish:
- `/scan`
- `/tf`
- `/tf_static`
- `/odom`
- `/joint_states`
- `/imu/data`

### Current workspace status

Observed from the current implementation:
- `/scan`: yes
- `/tf`: yes
- `/tf_static`: yes
- `/odom`: yes
- `/joint_states`: not yet correctly published for the real robot
- `/imu/data`: yes

### Recommended TF tree

- `map`
  - `odom`
    - `base_link`
      - `laser`
      - `camera_link`
      - `imu_link`

Optional but useful:
- `base_link` -> `base_footprint`

---

## 3) Odometry strategy recommendation

### Recommended architecture

Use:
- wheel encoder odometry as the primary low-level motion estimate
- IMU for rotation and short-term stability
- robot_localization EKF to fuse them into a filtered odometry output

Recommended output:
- `/odometry/filtered` from EKF
- Use this as the source for SLAM and Nav2

### Why encoder-only is not enough

Wheel-only odometry is especially weak for:
- rotation
- sideways motion
- diagonal motion
- wheel slip
- uneven floors

### Recommended sensor fusion stack

- `robot_localization`
- `ekf_filter_node_odom` for odom -> base_link
- `ekf_filter_node_map` for map -> odom when SLAM is active

---

## 4) SLAM Toolbox configuration recommendations

For a small indoor mapping robot, the recommended values are:

- resolution: `0.025`
- map_update_interval: `5.0`
- minimum_travel_distance: `0.08`
- minimum_travel_heading: `0.10`
- scan_buffer_size: `20`
- scan_queue_size: `10`
- solver: `solver_plugins::CeresSolver`
- loop_closing: `true`
- thread_num: `2`
- max_laser_range: `10.0`

Recommended for office/house/corridor mapping:
- Use a resolution of `0.025` to `0.03` for good indoor detail.
- Keep the robot speed below `0.3 m/s` for mapping.
- Avoid fast turns.
- Make sure the scan rate and odometry are stable before increasing speed.

---

## 5) Recommended mapping workflow

1. Start the robot
2. Launch the minimal compute stack
3. Launch SLAM
4. Drive slowly through the environment
5. Build the map
6. Save the map
7. Verify map quality
8. Launch localization
9. Launch Nav2
10. Navigate autonomously

Recommended operational rules:
- Maximum mapping speed: `0.20 - 0.30 m/s`
- Maximum angular velocity: `0.4 - 0.6 rad/s`
- Recommended acceleration: `0.4 m/s^2`
- Recommended deceleration: `0.6 m/s^2`

---

## 6) Recommended launch architecture

### Core launch files

- minimal.launch.py
  - robot_state_publisher
  - LiDAR
  - serial bridge
  - optional wheel odometry

- slam.launch.py
  - minimal stack
  - SLAM Toolbox

- localization.launch.py
  - map_server
  - AMCL or EKF-based localization

- nav2.launch.py
  - localization + Nav2 planner/controller/server

- ai.launch.py
  - AI node

- view_robot.launch.py
  - RViz2 on the desktop machine

- full_robot.launch.py
  - combines all components with optional RViz

### Recommended runtime split

- Raspberry Pi: sensing, control, localization, SLAM, low-level decisions
- Laptop/desktop: RViz, debugging, AI visualization, web dashboard, high-level monitoring

---

## 7) Recommended package architecture

Suggested packages:

- robot_bringup
  - launch files
  - configs
  - scripts
  - map storage

- robot_description
  - URDF/Xacro
  - meshes
  - sensor frames

- robot_serial
  - ESP32 bridge
  - encoder parser
  - wheel odometry
  - motor command interface

- robot_localization
  - EKF node integration

- robot_control
  - PID controller
  - velocity controller
  - motion command interface

- robot_navigation
  - Nav2 integration
  - costmap and planner config

- robot_ai
  - person detection / vision processing

- robot_web
  - dashboard and remote control

This structure is scalable for AI, voice interaction, person following, and future autonomy.

---

## 8) Recommended folder structure

```text
src/
  robot_bringup/
    launch/
    config/
    scripts/
    rviz/
    maps/
  robot_description/
    urdf/
    launch/
    config/
  robot_serial/
    robot_serial/
    launch/
    config/
  robot_control/
    robot_control/
    launch/
    config/
  robot_localization/
    config/
  robot_navigation/
    launch/
    config/
  robot_ai/
    robot_ai/
    launch/
    config/
  robot_web/
    launch/
    config/
```

---

## 9) Pre-Nav2 checklist

| Item | Why it matters | How to test | How to fix |
| --- | --- | --- | --- |
| LiDAR publishes /scan | SLAM and localization depend on it | `ros2 topic echo /scan` | Check LiDAR driver and frame id |
| TF tree is valid | Nav2 needs consistent transforms | `ros2 run tf2_tools view_frames` | Fix frame IDs and publishers |
| /tf and /tf_static exist | Navigation needs static and dynamic transforms | `ros2 topic list | grep tf` | Start robot_state_publisher and odometry node |
| /odom is stable | Bad odometry causes navigation drift | Drive a known path | Improve encoder quality and EKF fusion |
| /imu/data is present | IMU stabilizes rotation | Inspect IMU topic rate | Fix serial bridge and calibration |
| /joint_states exists | Visualization and model updates need it | `rostopic echo /joint_states` | Publish joint states from encoder data |
| SLAM map is consistent | Map errors break localization | Visually inspect the saved map | Tune SLAM parameters and improve odometry |
| Wheel geometry is calibrated | Geometry errors create drift | Drive a known distance | Re-measure wheel radius and separation |
| Mecanum kinematics are correct | Sideways motion must be modeled | Test left/right/diagonal movement | Replace differential odometry with Mecanum model |
| EKF fused odometry works | Better localization for Nav2 | Compare raw and filtered odometry | Add robot_localization |
| LiDAR mounting is stable | Unstable scan causes map noise | Observe scan quality while driving | Re-mount the sensor |
| Motor controller is stable | Control errors corrupt odometry | Test constant-speed commands | Tune PID and update rate |
| Serial link is reliable | Sensor loss harms mapping | Disconnect/reconnect and see recovery | Add checksums and watchdog |

---

## 10) Recommended parameter configuration

### slam_toolbox

See [src/robot_bringup/config/slam_toolbox_params.yaml](src/robot_bringup/config/slam_toolbox_params.yaml).

### robot_localization EKF

See [src/robot_bringup/config/ekf.yaml](src/robot_bringup/config/ekf.yaml).

---

## Final recommendation

The main upgrade path is:

1. Replace the current differential-drive odometry with a Mecanum-aware odometry node.
2. Fuse wheel odometry and IMU with robot_localization EKF.
3. Use the EKF output as the trusted source of `/odom` for SLAM and Nav2.
4. Tune SLAM Toolbox for indoor mapping and low-speed operation.
5. Make the TF tree, frame IDs, and topic names consistent.
6. Use the mapped and localized system only after the checklist above passes.
