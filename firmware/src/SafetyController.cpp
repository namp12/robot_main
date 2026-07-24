#include "SafetyController.h"

SafetyController::SafetyController()
    : _es_triggered(false), _status(STATUS_IDLE), _initialized(false),
      _last_command_ms(0) {}

bool SafetyController::init() {
  if (_initialized) return true;
  _es_triggered = false;
  _status = STATUS_IDLE;
  _initialized = true;
  return true;
}

void SafetyController::update(const SensorPacket& sensors) {
  if (!_initialized) return;

  if (_es_triggered) return;

  if (checkFrontObstacle(sensors.distance)) {
    triggerEStop("FRONT_OBSTACLE");
    return;
  }

  if (checkRearObstacle(sensors.distance)) {
    triggerEStop("REAR_OBSTACLE");
    return;
  }

  if (checkLowBattery(sensors.battery)) {
    triggerEStop("LOW_BATTERY");
    return;
  }

  updateStatus(sensors);
}

void SafetyController::triggerEStop(const char* reason) {
  _es_triggered = true;
  _es_reason = String(reason);
  _status = STATUS_ESTOP;
}

void SafetyController::clearEStop() {
  _es_triggered = false;
  _es_reason = "";
  _status = STATUS_IDLE;
}

bool SafetyController::isEStopped() const {
  return _es_triggered;
}

RobotStatus SafetyController::getStatus() const {
  return _status;
}

String SafetyController::getEStopReason() const {
  return _es_reason;
}

bool SafetyController::checkFrontObstacle(const DistanceData& dist) {
  return dist.front_valid && dist.front_cm < SAFE_DISTANCE_CM;
}

bool SafetyController::checkRearObstacle(const DistanceData& dist) {
  return dist.rear_valid && dist.rear_cm < SAFE_DISTANCE_CM;
}

bool SafetyController::checkLowBattery(const BatteryData& bat) {
  return bat.valid && bat.voltage < BATTERY_MIN_VOLTAGE;
}

void SafetyController::updateStatus(const SensorPacket& sensors) {
  if (_status == STATUS_ESTOP) return;

  if (sensors.battery.valid && sensors.battery.voltage < BATTERY_MIN_VOLTAGE + 0.5f) {
    _status = STATUS_LOW_BATTERY;
  } else {
    _status = STATUS_IDLE;
  }
}
