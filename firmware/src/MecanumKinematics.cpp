#include "MecanumKinematics.h"

void MecanumKinematics::compute(float vx, float vy, float wz, WheelSpeed& out) {
  float l = WHEEL_BASE;
  float w = TRACK_WIDTH;
  float scale = 255.0f;

  float v_fl = (vx + vy + wz * (l / 2.0f + w / 2.0f)) * scale;
  float v_fr = (vx - vy - wz * (l / 2.0f + w / 2.0f)) * scale;
  float v_rl = (vx - vy + wz * (l / 2.0f + w / 2.0f)) * scale;
  float v_rr = (vx + vy - wz * (l / 2.0f + w / 2.0f)) * scale;

  out.fl = (int16_t)constrain(v_fl, -255, 255);
  out.fr = (int16_t)constrain(v_fr, -255, 255);
  out.rl = (int16_t)constrain(v_rl, -255, 255);
  out.rr = (int16_t)constrain(v_rr, -255, 255);
  out.linear_x = vx;
  out.linear_y = vy;
  out.angular_z = wz;
}

void MecanumKinematics::normalize(WheelSpeed& speeds) {
  int16_t max_speed = max(max(abs(speeds.fl), abs(speeds.fr)),
                          max(abs(speeds.rl), abs(speeds.rr)));
  if (max_speed > MOTOR_MAX_SPEED) {
    float factor = (float)MOTOR_MAX_SPEED / (float)max_speed;
    speeds.fl = (int16_t)(speeds.fl * factor);
    speeds.fr = (int16_t)(speeds.fr * factor);
    speeds.rl = (int16_t)(speeds.rl * factor);
    speeds.rr = (int16_t)(speeds.rr * factor);
  }
}
