#include "EncoderManager.h"

EncoderManager* EncoderManager::_instance = nullptr;

EncoderManager::EncoderManager()
    : _count_fl(0), _count_fr(0), _count_rl(0), _count_rr(0),
      _last_update(0), _last_pulse_fl(0), _last_pulse_fr(0),
      _last_pulse_rl(0), _last_pulse_rr(0), _initialized(false) {
  memset(&_data, 0, sizeof(_data));
  _pins_fl[0] = ENCODER_FL_A;
  _pins_fl[1] = ENCODER_FL_B;
  _pins_fr[0] = ENCODER_FR_A;
  _pins_fr[1] = ENCODER_FR_B;
  _pins_rl[0] = ENCODER_RL_A;
  _pins_rl[1] = ENCODER_RL_B;
  _pins_rr[0] = ENCODER_RR_A;
  _pins_rr[1] = ENCODER_RR_B;
  _instance = this;
}

void IRAM_ATTR EncoderManager::onPulseFL() {
  if (_instance) _instance->_count_fl++;
}
void IRAM_ATTR EncoderManager::onPulseFR() {
  if (_instance) _instance->_count_fr++;
}
void IRAM_ATTR EncoderManager::onPulseRL() {
  if (_instance) _instance->_count_rl++;
}
void IRAM_ATTR EncoderManager::onPulseRR() {
  if (_instance) _instance->_count_rr++;
}

bool EncoderManager::init() {
  if (_initialized) return true;

  pinMode(_pins_fl[0], INPUT_PULLUP);
  pinMode(_pins_fl[1], INPUT_PULLUP);
  pinMode(_pins_fr[0], INPUT_PULLUP);
  pinMode(_pins_fr[1], INPUT_PULLUP);
  pinMode(_pins_rl[0], INPUT_PULLUP);
  pinMode(_pins_rl[1], INPUT_PULLUP);
  pinMode(_pins_rr[0], INPUT_PULLUP);
  pinMode(_pins_rr[1], INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(_pins_fl[0]), onPulseFL, RISING);
  attachInterrupt(digitalPinToInterrupt(_pins_fr[0]), onPulseFR, RISING);
  attachInterrupt(digitalPinToInterrupt(_pins_rl[0]), onPulseRL, RISING);
  attachInterrupt(digitalPinToInterrupt(_pins_rr[0]), onPulseRR, RISING);

  _last_update = millis();
  _initialized = true;
  return true;
}

void EncoderManager::update() {
  if (!_initialized) return;

  uint32_t now = millis();
  uint32_t dt = now - _last_update;
  if (dt < 50) return;

  noInterrupts();
  int32_t count_fl = _count_fl;
  int32_t count_fr = _count_fr;
  int32_t count_rl = _count_rl;
  int32_t count_rr = _count_rr;
  interrupts();

  uint32_t pulses_fl = count_fl - _last_pulse_fl;
  uint32_t pulses_fr = count_fr - _last_pulse_fr;
  uint32_t pulses_rl = count_rl - _last_pulse_rl;
  uint32_t pulses_rr = count_rr - _last_pulse_rr;

  const float pulses_per_rev = 20.0f * 4.0f;
  const float rpm_scale = 60000.0f / (pulses_per_rev * (float)dt);

  _data.fl = count_fl;
  _data.fr = count_fr;
  _data.rl = count_rl;
  _data.rr = count_rr;
  _data.fl_rpm = pulses_fl * rpm_scale;
  _data.fr_rpm = pulses_fr * rpm_scale;
  _data.rl_rpm = pulses_rl * rpm_scale;
  _data.rr_rpm = pulses_rr * rpm_scale;
  _data.timestamp = now;

  _last_pulse_fl = count_fl;
  _last_pulse_fr = count_fr;
  _last_pulse_rl = count_rl;
  _last_pulse_rr = count_rr;
  _last_update = now;
}

const EncoderData& EncoderManager::getData() const {
  return _data;
}

void EncoderManager::reset() {
  noInterrupts();
  _count_fl = 0;
  _count_fr = 0;
  _count_rl = 0;
  _count_rr = 0;
  _last_pulse_fl = 0;
  _last_pulse_fr = 0;
  _last_pulse_rl = 0;
  _last_pulse_rr = 0;
  interrupts();
  memset(&_data, 0, sizeof(_data));
}
