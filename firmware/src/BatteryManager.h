#ifndef BATTERY_MANAGER_H
#define BATTERY_MANAGER_H

#include <Arduino.h>
#include "config.h"

struct BatteryData {
  float voltage;
  float percentage;
  uint32_t timestamp;
  bool valid;
};

class BatteryManager {
 public:
  BatteryManager();
  bool init();
  void update();
  const BatteryData& getData() const;
  bool isLowBattery() const;

 private:
  BatteryData _data;
  uint8_t _adc_pin;
  bool _initialized;
  const float _adc_max = 4095.0f;
  const float _ref_voltage = 3.3f;
};

#endif
