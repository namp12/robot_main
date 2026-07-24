#include <Arduino.h>
#include "config.h"
#include "SerialProtocol.h"
#include "MotorDriver.h"
#include "MecanumKinematics.h"
#include "MotionController.h"
#include "EncoderManager.h"
#include "IMUManager.h"
#include "DistanceManager.h"
#include "BatteryManager.h"
#include "SensorManager.h"
#include "SafetyController.h"
#include "ModeManager.h"
#include "CommandParser.h"
#include "CommandExecutor.h"
#include "ROS2Interface.h"

MotionController motion;
SensorManager sensors;
SafetyController safety;
ModeManager mode_mgr;
CommandExecutor executor(mode_mgr, motion);
ROS2Interface ros2_iface;
bool ros2_mode = false;
uint32_t heartbeat_last = 0;
uint32_t telemetry_last = 0;

void setup() {
  Serial.begin(SERIAL_BAUDRATE);
  while (!Serial) delay(10);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  motion.init();
  sensors.init();
  safety.init();
  mode_mgr.init();

  Serial.println("MODE=MANUAL");
  Serial.println("STATUS=IDLE");
  Serial.println("SYSTEM_READY");
  Serial.println("FIRMWARE=" FIRMWARE_VERSION);
}

void loop() {
  uint32_t now = millis();

  if (mode_mgr.getMode() == MODE_ROS2) {
    ROS2Command cmd = ros2_iface.readCommand();
    if (cmd.set_mode) {
      mode_mgr.setMode(cmd.mode);
      ros2_mode = true;
    } else if (cmd.has_twist) {
      motion.setTwist(cmd.linear_x, cmd.linear_y, cmd.angular_z);
      mode_mgr.onCommandReceived();
    } else if (cmd.reset_yaw) {
      Serial.println("RESET_YAW received");
    }
  }

  if (mode_mgr.getMode() != MODE_ROS2) {
    if (Serial.available()) {
      String line = Serial.readStringUntil('\n');
      line.trim();
      if (line.length() > 0) {
        ParsedCommand cmd = CommandParser::parse(line);
        executor.execute(cmd);
        mode_mgr.onCommandReceived();
      }
    }
  }

  mode_mgr.update();
  sensors.update();
  safety.update(sensors.getPacket());

  if (safety.isEStopped()) {
    motion.stop();
  } else {
    motion.update();
  }

  if (now - telemetry_last > TELEMETRY_INTERVAL_MS) {
    telemetry_last = now;
    Serial.print(sensors.buildTelemetry());
    Serial.print("MODE=");
    Serial.println(mode_mgr.modeToString());
    Serial.print("STATUS=");
    Serial.println(statusToString(safety.getStatus()));
  }

  if (mode_mgr.isCommandTimeout() && mode_mgr.getMode() == MODE_ROS2) {
    mode_mgr.setMode(MODE_MANUAL);
    ros2_mode = false;
  }

  if (now - heartbeat_last > HEARTBEAT_INTERVAL_MS) {
    heartbeat_last = now;
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }

  delay(LOOP_INTERVAL_MS);
}
