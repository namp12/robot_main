#ifndef MODE_MANAGER_H
#define MODE_MANAGER_H

#include <Arduino.h>
#include "config.h"

class ModeManager {
 public:
  ModeManager();
  bool init();
  void update();
  void setMode(RobotMode mode);
  RobotMode getMode() const;
  void onCommandReceived();
  bool isCommandTimeout() const;
  String modeToString() const;

 private:
  RobotMode _current_mode;
  bool _initialized;
  uint32_t _last_command_ms;
  void applyMode(RobotMode mode);
};

#endif
