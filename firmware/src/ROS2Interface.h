#ifndef ROS2_INTERFACE_H
#define ROS2_INTERFACE_H

#include <Arduino.h>
#include "config.h"

struct ROS2Command {
  bool has_twist;
  float linear_x;
  float linear_y;
  float angular_z;
  bool set_mode;
  RobotMode mode;
  bool reset_yaw;
};

class ROS2Interface {
 public:
  ROS2Interface();
  ROS2Command readCommand();
  void sendTelemetry(const String& data);
  void sendStatus(RobotMode mode, RobotStatus status);
  bool parseFrame(const uint8_t* data, size_t len, ROS2Command& out);
  uint8_t buildFrame(uint8_t msg_id, const uint8_t* payload, uint16_t len,
                     uint8_t* out_buf);
  static uint16_t crc16(const uint8_t* data, uint16_t len);

 private:
  enum ParseState : uint8_t {
    ROS_IDLE = 0,
    ROS_HEADER = 1,
    ROS_MSG_ID = 2,
    ROS_LENGTH = 3,
    ROS_PAYLOAD = 4,
    ROS_CRC1 = 5,
    ROS_CRC2 = 6,
    ROS_TAIL = 7
  };
  ParseState _state;
  uint8_t _msg_id;
  uint8_t _length;
  uint8_t _payload[64];
  uint8_t _payload_idx;
  uint16_t _crc;
  uint8_t _rx_buffer[256];
  uint16_t _rx_len;
};

#endif
