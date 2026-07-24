#include "ModeManager.h"

ModeManager::ModeManager()
    : _current_mode(MODE_MANUAL), _initialized(false), _last_command_ms(0) {}

bool ModeManager::init() {
  if (_initialized) return true;
  _current_mode = MODE_MANUAL;
  _last_command_ms = millis();
  _initialized = true;
  return true;
}

void ModeManager::update() {
  if (isCommandTimeout()) {
    _current_mode = MODE_MANUAL;
  }
}

void ModeManager::setMode(RobotMode mode) {
  _current_mode = mode;
  _last_command_ms = millis();
  applyMode(mode);
}

RobotMode ModeManager::getMode() const {
  return _current_mode;
}

void ModeManager::onCommandReceived() {
  _last_command_ms = millis();
}

bool ModeManager::isCommandTimeout() const {
  return (millis() - _last_command_ms) > COMMAND_TIMEOUT_MS;
}

String ModeManager::modeToString() const {
  switch (_current_mode) {
    case MODE_MANUAL: return "MANUAL";
    case MODE_AUTO: return "AUTO";
    case MODE_ROS2: return "ROS2";
    case MODE_TEST: return "TEST";
    default: return "UNKNOWN";
  }
}

void ModeManager::applyMode(RobotMode mode) {
  _last_command_ms = millis();
}
