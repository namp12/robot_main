#ifndef MECANUM_KINEMATICS_H
#define MECANUM_KINEMATICS_H

#include <Arduino.h>
#include "config.h"

struct WheelSpeed {
  int16_t fl;
  int16_t fr;
  int16_t rl;
  int16_t rr;
  float linear_x;
  float linear_y;
  float angular_z;
};

class MecanumKinematics {
 public:
  static void compute(float vx, float vy, float wz, WheelSpeed& out);
  static void normalize(WheelSpeed& speeds);
};

#endif
