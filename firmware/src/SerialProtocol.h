#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>
#include "config.h"

class SerialProtocol {
 public:
  static String buildTelemetryLine(const String& key, const String& value);
  static String buildTelemetryLine(const char* key, float value);
  static String buildTelemetryLine(const char* key, int32_t value);
  static String buildMoveCommand(const char* direction, int16_t speed);
  static String buildModeCommand(RobotMode mode);
  static String buildConfigCommand(const char* param, float value);
  static String buildStatusString(RobotStatus status);
};

#endif
