#ifndef MOTION_CONTROLLER_H
#define MOTION_CONTROLLER_H

#include <Arduino.h>
#include "MotorDriver.h"
#include "MecanumKinematics.h"

class MotionController {
 public:
  MotionController();
  bool init();
  void update();
  void moveForward(int16_t speed);
  void moveBackward(int16_t speed);
  void moveStrafeLeft(int16_t speed);
  void moveStrafeRight(int16_t speed);
  void moveRotateLeft(int16_t speed);
  void moveRotateRight(int16_t speed);
  void moveDiagonalFrontLeft(int16_t speed);
  void moveDiagonalFrontRight(int16_t speed);
  void moveDiagonalRearLeft(int16_t speed);
  void moveDiagonalRearRight(int16_t speed);
  void stop();
  void setSpeed(int16_t speed);
  void setTwist(float vx, float vy, float wz);
  WheelSpeed getWheelSpeed() const;
  bool isEStopped() const;

 private:
  MotorDriver* _motors[4];
  WheelSpeed _current_speed;
  bool _es_triggered;
  int16_t _default_speed;
  void applyWheelSpeeds();
};

#endif
