#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include <Arduino.h>
#include "config.h"

struct MotorPins {
  uint8_t pwm_l;
  uint8_t pwm_r;
  uint8_t dir;
};

class MotorDriver {
 public:
  MotorDriver(const char* name, const MotorPins& pins);
  void init();
  void setSpeed(int16_t speed);
  void stop();
  int16_t getSpeed() const;
  const char* getName() const;

 private:
  const char* _name;
  MotorPins _pins;
  int16_t _speed;
  bool _initialized;
  void writePins(int16_t speed);
};

#endif
