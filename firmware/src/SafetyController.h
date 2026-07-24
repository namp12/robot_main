#ifndef SAFETY_CONTROLLER_H
#define SAFETY_CONTROLLER_H

#include <Arduino.h>
#include "config.h"
#include "SensorManager.h"

class SafetyController {
 public:
  SafetyController();
  bool init();
  void update(const SensorPacket& sensors);
  void triggerEStop(const char* reason);
  void clearEStop();
  bool isEStopped() const;
  RobotStatus getStatus() const;
  String getEStopReason() const;

 private:
  bool _es_triggered;
  String _es_reason;
  RobotStatus _status;
  bool _initialized;
  bool checkFrontObstacle(const DistanceData& dist);
  bool checkRearObstacle(const DistanceData& dist);
  bool checkLowBattery(const BatteryData& bat);
  uint32_t _last_command_ms;
  void updateStatus(const SensorPacket& sensors);
};

#endif
