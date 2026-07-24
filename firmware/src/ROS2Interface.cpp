#include "ROS2Interface.h"

ROS2Interface::ROS2Interface()
    : _state(ROS_IDLE), _msg_id(0), _length(0), _payload_idx(0),
      _crc(0), _rx_len(0) {}

uint16_t ROS2Interface::crc16(const uint8_t* data, uint16_t len) {
  uint16_t crc = 0xFFFF;
  for (uint16_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      if (crc & 0x0001) crc = (crc >> 1) ^ 0xA001;
      else crc >>= 1;
    }
  }
  return crc;
}

uint8_t ROS2Interface::buildFrame(uint8_t msg_id, const uint8_t* payload,
                                   uint16_t len, uint8_t* out_buf) {
  out_buf[0] = 0xFF;
  out_buf[1] = 0xFE;
  out_buf[2] = msg_id;
  out_buf[3] = (uint8_t)len;
  memcpy(&out_buf[4], payload, len);

  uint16_t crc_val = crc16(&out_buf[2], 2 + len);
  out_buf[4 + len] = (uint8_t)(crc_val & 0xFF);
  out_buf[5 + len] = (uint8_t)((crc_val >> 8) & 0xFF);
  out_buf[6 + len] = 0xFD;

  return 7 + len;
}

void ROS2Interface::sendTelemetry(const String& data) {
  Serial.println(data);
}

void ROS2Interface::sendStatus(RobotMode mode, RobotStatus status) {
  Serial.print("MODE=");
  Serial.print(modeToString(mode));
  Serial.print("\nSTATUS=");
  Serial.print(statusToString(status));
  Serial.print("\n");
}

ROS2Command ROS2Interface::readCommand() {
  ROS2Command cmd;
  cmd.has_twist = false;
  cmd.set_mode = false;
  cmd.reset_yaw = false;

  while (Serial.available() > 0 && _rx_len < 256) {
    uint8_t b = Serial.read();
    _rx_buffer[_rx_len++] = b;

    if (_state != ROS_IDLE && _rx_len > 100) {
      _state = ROS_IDLE;
      _rx_len = 0;
      continue;
    }

    if (_state == ROS_IDLE && b == 0xFF) {
      _state = ROS_HEADER;
      continue;
    }
    if (_state == ROS_HEADER && b == 0xFE) {
      _state = ROS_MSG_ID;
      _payload_idx = 0;
      continue;
    }

    if (_state == ROS_MSG_ID) {
      _msg_id = b;
      _state = ROS_LENGTH;
      _payload_idx = 0;
      continue;
    }

    if (_state == ROS_LENGTH) {
      _length = b;
      if (_length > 64) {
        _state = ROS_IDLE;
        _rx_len = 0;
        continue;
      }
      _state = ROS_PAYLOAD;
      _payload_idx = 0;
      continue;
    }

    if (_state == ROS_PAYLOAD) {
      _payload[_payload_idx++] = b;
      if (_payload_idx >= _length) {
        _state = ROS_CRC1;
      }
      continue;
    }

    if (_state == ROS_CRC1) {
      _crc = b;
      _state = ROS_CRC2;
      continue;
    }

    if (_state == ROS_CRC2) {
      _crc |= ((uint16_t)b << 8);

      uint8_t calc_buf[1 + 1 + 64];
      calc_buf[0] = _msg_id;
      calc_buf[1] = _length;
      memcpy(&calc_buf[2], _payload, _length);
      uint16_t calc_crc = crc16(calc_buf, 2 + _length);

      if (calc_crc == _crc) {
        if (_msg_id == 0x02 && _length == 12) {
          float vx, vy, wz;
          memcpy(&vx, &_payload[0], 4);
          memcpy(&vy, &_payload[4], 4);
          memcpy(&wz, &_payload[8], 4);
          cmd.has_twist = true;
          cmd.linear_x = vx;
          cmd.linear_y = vy;
          cmd.angular_z = wz;
        } else if (_msg_id == 0x03 && _length == 2) {
          cmd.set_mode = true;
          cmd.mode = (RobotMode)_payload[0];
        } else if (_msg_id == 0x04) {
          cmd.reset_yaw = true;
        }
      }

      _state = ROS_IDLE;
      _rx_len = 0;
      continue;
    }
  }

  return cmd;
}
