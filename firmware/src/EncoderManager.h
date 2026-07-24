#ifndef ENCODER_MANAGER_H
#define ENCODER_MANAGER_H

#include <Arduino.h>
#include "config.h"

struct EncoderData {
  int32_t fl;
  int32_t fr;
  int32_t rl;
  int32_t rr;
  float fl_rpm;
  float fr_rpm;
  float rl_rpm;
  float rr_rpm;
  uint32_t timestamp;
};

class EncoderManager {
 public:
  EncoderManager();
  bool init();
  void update();
  const EncoderData& getData() const;
  void reset();

 private:
  EncoderData _data;
  volatile int32_t _count_fl;
  volatile int32_t _count_fr;
  volatile int32_t _count_rl;
  volatile int32_t _count_rr;
  uint32_t _last_update;
  uint32_t _last_pulse_fl;
  uint32_t _last_pulse_fr;
  uint32_t _last_pulse_rl;
  uint32_t _last_pulse_rr;

  static void IRAM_ATTR onPulseFL();
  static void IRAM_ATTR onPulseFR();
  static void IRAM_ATTR onPulseRL();
  static void IRAM_ATTR onPulseRR();

  static EncoderManager* _instance;
  uint8_t _pins_fl[2];
  uint8_t _pins_fr[2];
  uint8_t _pins_rl[2];
  uint8_t _pins_rr[2];
  bool _initialized;
};

#endif
