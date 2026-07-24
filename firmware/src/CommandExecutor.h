#ifndef COMMAND_EXECUTOR_H
#define COMMAND_EXECUTOR_H

#include <Arduino.h>
#include "config.h"
#include "CommandParser.h"
#include "ModeManager.h"

class MotionController;

class CommandExecutor {
 public:
  CommandExecutor(ModeManager& mode_mgr, MotionController& motion);
  void execute(const ParsedCommand& cmd);

 private:
  ModeManager& _mode_mgr;
  MotionController& _motion;
  float _safe_distance;
  uint32_t _command_timeout_ms;

  bool canMove() const;
};

#endif
