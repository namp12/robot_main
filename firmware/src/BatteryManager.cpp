#include "BatteryManager.h"

BatteryManager::BatteryManager()
    : _adc_pin(BATTERY_ADC_PIN), _initialized(false) {
  memset(&_data, 0, sizeof(_data));
}

bool BatteryManager::init() {
  if (_initialized) return true;
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  _initialized = true;
  _data.timestamp = millis();
  return true;
}

void BatteryManager::update() {
  if (!_initialized) return;

  uint32_t now = millis();
  if (now - _data.timestamp < 2000) return;

  int raw = analogRead(_adc_pin);
  float v_adc = (raw / _adc_max) * _ref_voltage;
  float v_battery = v_adc * VOLTAGE_DIVIDER_RATIO;

  _data.voltage = v_battery;
  _data.percentage = ((v_battery - BATTERY_MIN_VOLTAGE) /
                      (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)) * 100.0f;
  _data.percentage = constrain(_data.percentage, 0.0f, 100.0f);
  _data.valid = true;
  _data.timestamp = now;
}

const BatteryData& BatteryManager::getData() const {
  return _data;
}

bool BatteryManager::isLowBattery() const {
  return _data.valid && _data.voltage < BATTERY_MIN_VOLTAGE;
}
