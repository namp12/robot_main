#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ========== SYSTEM ==========
#define FIRMWARE_VERSION "1.0.0"
#define FIRMWARE_NAME "RobotOS ESP32 Firmware"
#define LED_BUILTIN 2

// ========== TIMING ==========
#define LOOP_INTERVAL_MS 10
#define TELEMETRY_INTERVAL_MS 50
#define COMMAND_TIMEOUT_MS 2000
#define HEARTBEAT_INTERVAL_MS 1000
#define SAFETY_CHECK_INTERVAL_MS 50

// ========== SERIAL ==========
#define SERIAL_BAUDRATE 115200
#define SERIAL_RX_BUFFER_SIZE 256

// ========== MOTOR / DRIVER ==========
#define MOTOR_PWM_FREQUENCY 20000
#define MOTOR_PWM_RESOLUTION 8
#define MOTOR_MAX_SPEED 255
#define MOTOR_DEFAULT_SPEED 150
#define MOTOR_TEST_SPEED 180
#define MOTOR_TEST_DURATION_MS 2000

#define WHEEL_BASE 0.20f
#define TRACK_WIDTH 0.18f
#define WHEEL_RADIUS 0.035f

// ========== ENCODER ==========
#define ENCODER_PPB 12
#define ENCODER_DEBOUNCE_US 10

// ========== SENSORS ==========
#define SAFE_DISTANCE_CM 30.0f
#define DISTANCE_MAX_CM 400.0f
#define BATTERY_MIN_VOLTAGE 9.0f
#define BATTERY_MAX_VOLTAGE 14.4f

// ========== IMU ==========
#define IMU_SDA_PIN 21
#define IMU_SCL_PIN 22
#define IMU_I2C_FREQ 400000
#define IMU_ACCEL_RANGE MPU6050_RANGE_2G
#define IMU_GYRO_RANGE MPU6050_RANGE_250DEG

// ========== I2C ==========
#define I2C_TIMEOUT_MS 100

// ========== BTS7960 PINOUT (customize to your wiring) ==========
// Format: {PWM_L, PWM_R, DIR}
#define MOTOR_FL {25, 26, 27}
#define MOTOR_FR {14, 12, 13}
#define MOTOR_RL {23, 19, 18}
#define MOTOR_RR {5, 17, 16}

// ========== ENCODER PINOUT ==========
#define ENCODER_FL_A 36
#define ENCODER_FL_B 39
#define ENCODER_FR_A 34
#define ENCODER_FR_B 35
#define ENCODER_RL_A 32
#define ENCODER_RL_B 33
#define ENCODER_RR_A 15
#define ENCODER_RR_B 4

// ========== SENSOR PINOUT ==========
#define TRIG_FRONT_PIN 2
#define ECHO_FRONT_PIN 4
#define TRIG_REAR_PIN 5
#define ECHO_REAR_PIN 18
#define BATTERY_ADC_PIN 35
#define VOLTAGE_DIVIDER_RATIO 2.0f

// ========== MODES ==========
enum RobotMode : uint8_t {
  MODE_MANUAL = 0,
  MODE_AUTO = 1,
  MODE_ROS2 = 2,
  MODE_TEST = 3
};

inline const char* modeToString(RobotMode mode) {
  switch (mode) {
    case MODE_MANUAL: return "MANUAL";
    case MODE_AUTO: return "AUTO";
    case MODE_ROS2: return "ROS2";
    case MODE_TEST: return "TEST";
    default: return "UNKNOWN";
  }
}

// ========== STATUS ==========
enum RobotStatus : uint8_t {
  STATUS_IDLE = 0,
  STATUS_RUNNING = 1,
  STATUS_ERROR = 2,
  STATUS_ESTOP = 3,
  STATUS_LOW_BATTERY = 4
};

inline const char* statusToString(RobotStatus status) {
  switch (status) {
    case STATUS_IDLE: return "IDLE";
    case STATUS_RUNNING: return "RUNNING";
    case STATUS_ERROR: return "ERROR";
    case STATUS_ESTOP: return "ESTOP";
    case STATUS_LOW_BATTERY: return "LOW_BATTERY";
    default: return "UNKNOWN";
  }
}

#endif
