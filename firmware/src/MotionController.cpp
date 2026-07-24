#include "MotionController.h"
#include "config.h"

MotionController::MotionController()
    : _es_triggered(false), _default_speed(MOTOR_DEFAULT_SPEED) {}

bool MotionController::init() {
  MotorPins fl_pins = MOTOR_FL;
  MotorPins fr_pins = MOTOR_FR;
  MotorPins rl_pins = MOTOR_RL;
  MotorPins rr_pins = MOTOR_RR;

  _motors[0] = new MotorDriver("FL", fl_pins);
  _motors[1] = new MotorDriver("FR", fr_pins);
  _motors[2] = new MotorDriver("RL", rl_pins);
  _motors[3] = new MotorDriver("RR", rr_pins);

  for (int i = 0; i < 4; i++) {
    _motors[i]->init();
  }

  stop();
  return true;
}

void MotionController::update() {
  if (_es_triggered) {
    stop();
    return;
  }
  applyWheelSpeeds();
}

void MotionController::applyWheelSpeeds() {
  for (int i = 0; i < 4; i++) {
    if (_motors[i]) {
      int16_t s = 0;
      switch (i) {
        case 0: s = _current_speed.fl; break;
        case 1: s = _current_speed.fr; break;
        case 2: s = _current_speed.rl; break;
        case 3: s = _current_speed.rr; break;
      }
      _motors[i]->setSpeed(s);
    }
  }
}

void MotionController::moveForward(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(s, 0.0f, 0.0f, _current_speed);
}

void MotionController::moveBackward(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(-s, 0.0f, 0.0f, _current_speed);
}

void MotionController::moveStrafeLeft(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(0.0f, s, 0.0f, _current_speed);
}

void MotionController::moveStrafeRight(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(0.0f, -s, 0.0f, _current_speed);
}

void MotionController::moveRotateLeft(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(0.0f, 0.0f, s, _current_speed);
}

void MotionController::moveRotateRight(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(0.0f, 0.0f, -s, _current_speed);
}

void MotionController::moveDiagonalFrontLeft(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(s, s, 0.0f, _current_speed);
}

void MotionController::moveDiagonalFrontRight(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(s, -s, 0.0f, _current_speed);
}

void MotionController::moveDiagonalRearLeft(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(-s, s, 0.0f, _current_speed);
}

void MotionController::moveDiagonalRearRight(int16_t speed) {
  if (_es_triggered) return;
  int16_t s = speed > 0 ? speed : _default_speed;
  MecanumKinematics::compute(-s, -s, 0.0f, _current_speed);
}

void MotionController::stop() {
  _current_speed.fl = 0;
  _current_speed.fr = 0;
  _current_speed.rl = 0;
  _current_speed.rr = 0;
  _es_triggered = false;
  for (int i = 0; i < 4; i++) {
    if (_motors[i]) {
      _motors[i]->stop();
    }
  }
}

void MotionController::setSpeed(int16_t speed) {
  if (_es_triggered) return;
  _default_speed = constrain(speed, 0, MOTOR_MAX_SPEED);
}

void MotionController::setTwist(float vx, float vy, float wz) {
  if (_es_triggered) return;
  MecanumKinematics::compute(vx, vy, wz, _current_speed);
  MecanumKinematics::normalize(_current_speed);
}

WheelSpeed MotionController::getWheelSpeed() const {
  return _current_speed;
}

bool MotionController::isEStopped() const {
  return _es_triggered;
}
