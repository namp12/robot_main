#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

#include <Arduino.h>
#include "config.h"

struct ParsedCommand {
  String type;
  String param1;
  float value1;
  float value2;
  bool valid;
};

class CommandParser {
 public:
  static ParsedCommand parse(const String& line);
};

#endif
