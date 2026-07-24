#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>
#include "IMUManager.h"
#include "EncoderManager.h"
#include "DistanceManager.h"
#include "BatteryManager.h"

struct SensorPacket {
  IMUData imu;
  EncoderData encoder;
  DistanceData distance;
  BatteryData battery;
  uint32_t timestamp;
};

class SensorManager {
 public:
  SensorManager();
  bool init();
  void update();
  const SensorPacket& getPacket() const;
  String buildTelemetry() const;
  bool isDataFresh() const;

 private:
  SensorManager(const SensorManager&);
  SensorManager& operator=(const SensorManager&);

  SensorPacket _packet;
  IMUManager _imu;
  EncoderManager _encoder;
  DistanceManager _distance;
  BatteryManager _battery;
  bool _initialized;
  void updateSensors();
};

#endif
