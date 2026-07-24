#include "SerialProtocol.h"

String SerialProtocol::buildTelemetryLine(const String& key, const String& value) {
  return key + "=" + value + "\n";
}

String SerialProtocol::buildTelemetryLine(const char* key, float value) {
  return String(key) + "=" + String(value, 2) + "\n";
}

String SerialProtocol::buildTelemetryLine(const char* key, int32_t value) {
  return String(key) + "=" + String(value) + "\n";
}

String SerialProtocol::buildMoveCommand(const char* direction, int16_t speed) {
  return String("MOVE ") + direction + " " + String(speed) + "\n";
}

String SerialProtocol::buildModeCommand(RobotMode mode) {
  switch (mode) {
    case MODE_MANUAL: return "MODE MANUAL\n";
    case MODE_AUTO: return "MODE AUTO\n";
    case MODE_ROS2: return "MODE ROS\n";
    case MODE_TEST: return "MODE TEST\n";
    default: return "MODE MANUAL\n";
  }
}

String SerialProtocol::buildConfigCommand(const char* param, float value) {
  return String("SET_") + param + " " + String(value, 1) + "\n";
}

String SerialProtocol::buildStatusString(RobotStatus status) {
  switch (status) {
    case STATUS_RUNNING: return "RUNNING";
    case STATUS_ESTOP: return "ESTOP";
    case STATUS_ERROR: return "ERROR";
    case STATUS_LOW_BATTERY: return "LOW_BATTERY";
    default: return "IDLE";
  }
}
