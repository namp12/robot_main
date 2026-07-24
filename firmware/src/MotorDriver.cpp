#include "MotorDriver.h"

MotorDriver::MotorDriver(const char* name, const MotorPins& pins)
    : _name(name), _pins(pins), _speed(0), _initialized(false) {}

void MotorDriver::init() {
  pinMode(_pins.pwm_l, OUTPUT);
  pinMode(_pins.pwm_r, OUTPUT);
  pinMode(_pins.dir, OUTPUT);
  digitalWrite(_pins.pwm_l, LOW);
  digitalWrite(_pins.pwm_r, LOW);
  digitalWrite(_pins.dir, LOW);
  _initialized = true;
  _speed = 0;
}

void MotorDriver::setSpeed(int16_t speed) {
  if (!_initialized) return;
  _speed = constrain(speed, -MOTOR_MAX_SPEED, MOTOR_MAX_SPEED);
  writePins(_speed);
}

void MotorDriver::stop() {
  setSpeed(0);
}

int16_t MotorDriver::getSpeed() const {
  return _speed;
}

const char* MotorDriver::getName() const {
  return _name;
}

void MotorDriver::writePins(int16_t speed) {
  if (speed > 0) {
    digitalWrite(_pins.dir, HIGH);
    analogWrite(_pins.pwm_l, speed);
    analogWrite(_pins.pwm_r, LOW);
  } else if (speed < 0) {
    digitalWrite(_pins.dir, LOW);
    analogWrite(_pins.pwm_l, abs(speed));
    analogWrite(_pins.pwm_r, LOW);
  } else {
    digitalWrite(_pins.dir, LOW);
    analogWrite(_pins.pwm_l, 0);
    analogWrite(_pins.pwm_r, 0);
  }
}
