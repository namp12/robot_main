#include "IMUManager.h"

IMUManager::IMUManager()
    : _initialized(false) {
  memset(&_data, 0, sizeof(_data));
}

bool IMUManager::init() {
  if (_initialized) return true;

  Wire.begin(IMU_SDA_PIN, IMU_SCL_PIN);
  Wire.setClock(IMU_I2C_FREQ);

  Wire.beginTransmission(0x68);
  if (Wire.endTransmission() != 0) {
    return false;
  }

  Wire.beginTransmission(0x68);
  Wire.write(0x6B);
  Wire.write(0x00);
  Wire.endTransmission();

  delay(100);
  _initialized = true;
  return true;
}

void IMUManager::update() {
  if (!_initialized) return;

  _data.valid = false;
  _data.timestamp = millis();

  Wire.beginTransmission(0x68);
  Wire.write(0x3B);
  if (Wire.endTransmission() != 0) return;

  uint8_t available = Wire.requestFrom(0x68, 14);
  if (available != 14) return;

  int16_t ax_raw = (int16_t)(Wire.read() << 8 | Wire.read());
  int16_t ay_raw = (int16_t)(Wire.read() << 8 | Wire.read());
  int16_t az_raw = (int16_t)(Wire.read() << 8 | Wire.read());
  int16_t gx_raw = (int16_t)(Wire.read() << 8 | Wire.read());
  int16_t gy_raw = (int16_t)(Wire.read() << 8 | Wire.read());
  int16_t gz_raw = (int16_t)(Wire.read() << 8 | Wire.read());
  int16_t temp_raw = (int16_t)(Wire.read() << 8 | Wire.read());

  const float accel_scale = 16384.0f;
  const float gyro_scale = 131.0f;

  _data.ax = ax_raw / accel_scale;
  _data.ay = ay_raw / accel_scale;
  _data.az = az_raw / accel_scale;
  _data.gx = gx_raw / gyro_scale;
  _data.gy = gy_raw / gyro_scale;
  _data.gz = gz_raw / gyro_scale;

  _data.valid = true;
}

const IMUData& IMUManager::getData() const {
  return _data;
}

void IMUManager::calibrate() {
  _initialized = false;
  init();
}
