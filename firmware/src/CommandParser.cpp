#include "CommandParser.h"

ParsedCommand CommandParser::parse(const String& line) {
  ParsedCommand cmd;
  cmd.valid = false;
  cmd.type = "";
  cmd.param1 = "";
  cmd.value1 = 0;
  cmd.value2 = 0;

  String trimmed = line;
  trimmed.trim();
  if (trimmed.length() == 0) return cmd;

  String working = trimmed;
  working.toUpperCase();

  int space_idx = working.indexOf(' ');
  String command;
  String params;

  if (space_idx > 0) {
    command = working.substring(0, space_idx);
    params = working.substring(space_idx + 1);
    params.trim();
  } else {
    command = working;
    params = "";
  }

  cmd.type = command;

  if (command == "MOVE") {
    if (params.length() == 0) return cmd;
    int p = params.indexOf(' ');
    String direction;
    String speed_str;

    if (p > 0) {
      direction = params.substring(0, p);
      speed_str = params.substring(p + 1);
      speed_str.trim();
    } else {
      direction = params;
      speed_str = String(MOTOR_DEFAULT_SPEED);
    }

    cmd.param1 = direction;
    cmd.value1 = speed_str.toFloat();
    cmd.value2 = cmd.value1;
    cmd.valid = true;
    return cmd;
  }

  if (command == "MODE") {
    if (params.length() == 0) return cmd;
    cmd.param1 = params;
    cmd.valid = true;
    return cmd;
  }

  if (command.startsWith("SET_")) {
    cmd.value1 = params.toFloat();
    cmd.valid = true;
    return cmd;
  }

  if (command == "STOP") {
    cmd.valid = true;
    return cmd;
  }

  if (command == "MODE") {
    cmd.valid = true;
    return cmd;
  }

  cmd.valid = true;
  return cmd;
}
