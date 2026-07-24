#include "SensorManager.h"

SensorManager::SensorManager() : _initialized(false) {
  memset(&_packet, 0, sizeof(_packet));
}

bool SensorManager::init() {
  if (_initialized) return true;

  if (!_imu.init()) return false;
  if (!_encoder.init()) return false;
  if (!_distance.init()) return false;
  if (!_battery.init()) return false;

  _initialized = true;
  _packet.timestamp = millis();
  return true;
}

void SensorManager::update() {
  if (!_initialized) return;
  updateSensors();
}

void SensorManager::updateSensors() {
  _imu.update();
  _encoder.update();
  _distance.update();
  _battery.update();

  _packet.imu = _imu.getData();
  _packet.encoder = _encoder.getData();
  _packet.distance = _distance.getData();
  _packet.battery = _battery.getData();
  _packet.timestamp = millis();
}

const SensorPacket& SensorManager::getPacket() const {
  return _packet;
}

String SensorManager::buildTelemetry() const {
  const SensorPacket& p = _packet;

  String imu_str = "IMU=" + String(p.imu.ax, 3) + "," +
                   String(p.imu.ay, 3) + "," +
                   String(p.imu.az, 3) + "," +
                   String(p.imu.gx, 3) + "," +
                   String(p.imu.gy, 3) + "," +
                   String(p.imu.gz, 3);

  String enc_str = "ENCODER=" + String(p.encoder.fl) + "," +
                   String(p.encoder.fr) + "," +
                   String(p.encoder.rl) + "," +
                   String(p.encoder.rr);

  String dist_str = "FRONT_DISTANCE=" + String(p.distance.front_cm, 1) +
                    ",REAR_DISTANCE=" + String(p.distance.rear_cm, 1);

  String bat_str = "BATTERY=" + String(p.battery.voltage, 2);

  return imu_str + "\n" + enc_str + "\n" + dist_str + "\n" + bat_str + "\n";
}

bool SensorManager::isDataFresh() const {
  uint32_t now = millis();
  return (now - _packet.timestamp) < 2000;
}
