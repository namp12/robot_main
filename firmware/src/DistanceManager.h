#ifndef DISTANCE_MANAGER_H
#define DISTANCE_MANAGER_H

#include <Arduino.h>
#include "config.h"

struct DistanceData {
  float front_cm;
  float rear_cm;
  uint32_t timestamp;
  bool front_valid;
  bool rear_valid;
};

class DistanceManager {
 public:
  DistanceManager();
  bool init();
  void update();
  const DistanceData& getData() const;

 private:
  DistanceData _data;
  uint8_t _trig_front;
  uint8_t _echo_front;
  uint8_t _trig_rear;
  uint8_t _echo_rear;
  bool _initialized;
  float readDistance(uint8_t trig_pin, uint8_t echo_pin);
};

#endif
