#include "DistanceManager.h"

DistanceManager::DistanceManager()
    : _trig_front(TRIG_FRONT_PIN), _echo_front(ECHO_FRONT_PIN),
      _trig_rear(TRIG_REAR_PIN), _echo_rear(ECHO_REAR_PIN),
      _initialized(false) {
  memset(&_data, 0, sizeof(_data));
}

bool DistanceManager::init() {
  if (_initialized) return true;

  pinMode(_trig_front, OUTPUT);
  pinMode(_echo_front, INPUT);
  pinMode(_trig_rear, OUTPUT);
  pinMode(_echo_rear, INPUT);

  digitalWrite(_trig_front, LOW);
  digitalWrite(_trig_rear, LOW);
  delay(50);

  _data.front_cm = DISTANCE_MAX_CM;
  _data.rear_cm = DISTANCE_MAX_CM;
  _data.front_valid = false;
  _data.rear_valid = false;
  _initialized = true;
  return true;
}

float DistanceManager::readDistance(uint8_t trig_pin, uint8_t echo_pin) {
  digitalWrite(trig_pin, LOW);
  delayMicroseconds(2);
  digitalWrite(trig_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_pin, LOW);

  long duration = pulseIn(echo_pin, HIGH, 30000);
  if (duration == 0) return DISTANCE_MAX_CM;

  float distance = duration * 0.0343f / 2.0f;
  return constrain(distance, 0.0f, DISTANCE_MAX_CM);
}

void DistanceManager::update() {
  if (!_initialized) return;

  static uint32_t last_read = 0;
  uint32_t now = millis();
  if (now - last_read < 100) return;
  last_read = now;

  _data.front_cm = readDistance(_trig_front, _echo_front);
  _data.rear_cm = readDistance(_trig_rear, _echo_rear);
  _data.front_valid = _data.front_cm < DISTANCE_MAX_CM;
  _data.rear_valid = _data.rear_cm < DISTANCE_MAX_CM;
  _data.timestamp = now;
}

const DistanceData& DistanceManager::getData() const {
  return _data;
}
