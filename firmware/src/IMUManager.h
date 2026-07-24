#ifndef IMU_MANAGER_H
#define IMU_MANAGER_H

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

struct IMUData {
  float ax;
  float ay;
  float az;
  float gx;
  float gy;
  float gz;
  uint32_t timestamp;
  bool valid;
};

class IMUManager {
 public:
  IMUManager();
  bool init();
  void update();
  const IMUData& getData() const;
  void calibrate();

 private:
  IMUData _data;
  bool _initialized;
  void parseIMU();
};

#endif
