#include "CommandExecutor.h"
#include "MotionController.h"

CommandExecutor::CommandExecutor(ModeManager& mode_mgr, MotionController& motion)
    : _mode_mgr(mode_mgr), _motion(motion) {
  _safe_distance = SAFE_DISTANCE_CM;
  _command_timeout_ms = COMMAND_TIMEOUT_MS;
}

void CommandExecutor::execute(const ParsedCommand& cmd) {
  if (!cmd.valid) return;

  String type = cmd.type;
  String param = cmd.param1;
  param.trim();
  param.toUpperCase();

  if (type == "MODE") {
    if (param == "MANUAL") _mode_mgr.setMode(MODE_MANUAL);
    else if (param == "AUTO") _mode_mgr.setMode(MODE_AUTO);
    else if (param == "ROS") _mode_mgr.setMode(MODE_ROS2);
    else if (param == "TEST") _mode_mgr.setMode(MODE_TEST);
    return;
  }

  if (type == "SET_SAFE_DISTANCE") {
    _safe_distance = constrain(cmd.value1, 5.0f, 200.0f);
    return;
  }

  if (type == "SET_TIMEOUT") {
    _command_timeout_ms = constrain((uint32_t)cmd.value1, 500, 30000);
    return;
  }

  if (type == "MOVE") {
    RobotMode mode = _mode_mgr.getMode();
    if (mode == MODE_MANUAL || mode == MODE_AUTO || mode == MODE_TEST) {
      int16_t speed = (int16_t)constrain(cmd.value1, 0, MOTOR_MAX_SPEED);
      if (param == "FORWARD") _motion.moveForward(speed);
      else if (param == "BACKWARD") _motion.moveBackward(speed);
      else if (param == "STRAFE_LEFT") _motion.moveStrafeLeft(speed);
      else if (param == "STRAFE_RIGHT") _motion.moveStrafeRight(speed);
      else if (param == "ROTATE_LEFT") _motion.moveRotateLeft(speed);
      else if (param == "ROTATE_RIGHT") _motion.moveRotateRight(speed);
      else if (param == "DIAGONAL_FRONT_LEFT") _motion.moveDiagonalFrontLeft(speed);
      else if (param == "DIAGONAL_FRONT_RIGHT") _motion.moveDiagonalFrontRight(speed);
      else if (param == "DIAGONAL_REAR_LEFT") _motion.moveDiagonalRearLeft(speed);
      else if (param == "DIAGONAL_REAR_RIGHT") _motion.moveDiagonalRearRight(speed);
      else if (param == "STOP") _motion.stop();
    }
  }
}
