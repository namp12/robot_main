#include <Arduino.h>
#include "config.h"
#include "MotorDriver.h"
#include "EncoderManager.h"
#include "SerialProtocol.h"

MotorDriver* motors[4];
EncoderManager encoder;
uint32_t last_telemetry = 0;
uint8_t test_state = 0;
uint32_t test_start = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  MotorPins fl = MOTOR_FL;
  MotorPins fr = MOTOR_FR;
  MotorPins rl = MOTOR_RL;
  MotorPins rr = MOTOR_RR;

  motors[0] = new MotorDriver("FL", fl);
  motors[1] = new MotorDriver("FR", fr);
  motors[2] = new MotorDriver("RL", rl);
  motors[3] = new MotorDriver("RR", rr);

  for (int i = 0; i < 4; i++) {
    motors[i]->init();
  }

  encoder.init();

  pinMode(LED_BUILTIN, OUTPUT);
  Serial.println("TEST_MOTOR_START");
  Serial.println("Type command: FORWARD <speed>, BACKWARD <speed>, STOP, ENCODER, DIAG <speed>");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    line.toUpperCase();

    if (line.startsWith("FORWARD")) {
      int speed = line.substring(8).toInt();
      motors[0]->setSpeed(speed);
      motors[1]->setSpeed(speed);
      motors[2]->setSpeed(speed);
      motors[3]->setSpeed(speed);
      Serial.print("FORWARD speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("BACKWARD")) {
      int speed = -line.substring(9).toInt();
      motors[0]->setSpeed(speed);
      motors[1]->setSpeed(speed);
      motors[2]->setSpeed(speed);
      motors[3]->setSpeed(speed);
      Serial.print("BACKWARD speed=");
      Serial.println(abs(speed));
    }

    else if (line.startsWith("STRAFE_LEFT")) {
      int speed = line.substring(12).toInt();
      motors[0]->setSpeed(speed);
      motors[1]->setSpeed(-speed);
      motors[2]->setSpeed(-speed);
      motors[3]->setSpeed(speed);
      Serial.print("STRAFE_LEFT speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("STRAFE_RIGHT")) {
      int speed = line.substring(13).toInt();
      motors[0]->setSpeed(-speed);
      motors[1]->setSpeed(speed);
      motors[2]->setSpeed(speed);
      motors[3]->setSpeed(-speed);
      Serial.print("STRAFE_RIGHT speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("ROTATE_LEFT")) {
      int speed = line.substring(12).toInt();
      motors[0]->setSpeed(speed);
      motors[1]->setSpeed(-speed);
      motors[2]->setSpeed(speed);
      motors[3]->setSpeed(-speed);
      Serial.print("ROTATE_LEFT speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("ROTATE_RIGHT")) {
      int speed = line.substring(13).toInt();
      motors[0]->setSpeed(-speed);
      motors[1]->setSpeed(speed);
      motors[2]->setSpeed(-speed);
      motors[3]->setSpeed(speed);
      Serial.print("ROTATE_RIGHT speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("DIAGONAL_FRONT_LEFT")) {
      int speed = line.substring(20).toInt();
      motors[0]->setSpeed(speed);
      motors[1]->setSpeed(0);
      motors[2]->setSpeed(0);
      motors[3]->setSpeed(speed);
      Serial.print("DIAGONAL_FRONT_LEFT speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("DIAGONAL_FRONT_RIGHT")) {
      int speed = line.substring(21).toInt();
      motors[0]->setSpeed(0);
      motors[1]->setSpeed(speed);
      motors[2]->setSpeed(speed);
      motors[3]->setSpeed(0);
      Serial.print("DIAGONAL_FRONT_RIGHT speed=");
      Serial.println(speed);
    }

    else if (line.startsWith("STOP")) {
      for (int i = 0; i < 4; i++) {
        motors[i]->stop();
      }
      Serial.println("STOP");
    }

    else if (line.startsWith("ENCODER")) {
      encoder.update();
      const EncoderData& d = encoder.getData();
      Serial.print("ENCODER=");
      Serial.print(d.fl); Serial.print(",");
      Serial.print(d.fr); Serial.print(",");
      Serial.print(d.rl); Serial.print(",");
      Serial.println(d.rr);
    }

    else if (line.startsWith("HELP")) {
      Serial.println("Commands: FORWARD <0-255>, BACKWARD <0-255>, STRAFE_LEFT <0-255>, STRAFE_RIGHT <0-255>, ROTATE_LEFT <0-255>, ROTATE_RIGHT <0-255>, DIAGONAL_FRONT_LEFT <0-255>, DIAGONAL_FRONT_RIGHT <0-255>, STOP, ENCODER");
    }

    else {
      Serial.println("Unknown command. Type HELP for list.");
    }
  }

  uint32_t now = millis();
  if (now - last_telemetry > 1000) {
    encoder.update();
    const EncoderData& d = encoder.getData();
    Serial.print("ENCODER=");
    Serial.print(d.fl); Serial.print(",");
    Serial.print(d.fr); Serial.print(",");
    Serial.print(d.rl); Serial.print(",");
    Serial.println(d.rr);
    last_telemetry = now;
  }
}
