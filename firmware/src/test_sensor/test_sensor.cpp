#include <Arduino.h>
#include "config.h"
#include "IMUManager.h"
#include "EncoderManager.h"
#include "DistanceManager.h"
#include "BatteryManager.h"
#include "SerialProtocol.h"

IMUManager imu;
EncoderManager encoder;
DistanceManager distance;
BatteryManager battery;

uint32_t last_telemetry = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  Serial.println("TEST_SENSOR_START");

  if (!imu.init()) {
    Serial.println("IMU init failed");
  }

  if (!encoder.init()) {
    Serial.println("Encoder init failed");
  }

  if (!distance.init()) {
    Serial.println("Distance init failed");
  }

  if (!battery.init()) {
    Serial.println("Battery init failed");
  }

  Serial.println("Sensors initialized. Type: IMU, ENCODER, DISTANCE, BATTERY, ALL");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    line.toUpperCase();

    if (line.startsWith("IMU")) {
      imu.update();
      const IMUData& d = imu.getData();
      Serial.print("IMU=ax:");
      Serial.print(d.ax, 3);
      Serial.print(",ay:");
      Serial.print(d.ay, 3);
      Serial.print(",az:");
      Serial.print(d.az, 3);
      Serial.print(",gx:");
      Serial.print(d.gx, 3);
      Serial.print(",gy:");
      Serial.print(d.gy, 3);
      Serial.print(",gz:");
      Serial.println(d.gz, 3);
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

    else if (line.startsWith("DISTANCE")) {
      distance.update();
      const DistanceData& d = distance.getData();
      Serial.print("FRONT_DISTANCE=");
      Serial.print(d.front_cm, 1);
      Serial.print(",REAR_DISTANCE=");
      Serial.println(d.rear_cm, 1);
    }

    else if (line.startsWith("BATTERY")) {
      battery.update();
      const BatteryData& d = battery.getData();
      Serial.print("BATTERY=");
      Serial.print(d.voltage, 2);
      Serial.print(",PERCENT=");
      Serial.println(d.percentage, 1);
    }

    else if (line.startsWith("ALL")) {
      imu.update();
      encoder.update();
      distance.update();
      battery.update();

      const IMUData& imu_d = imu.getData();
      const EncoderData& enc_d = encoder.getData();
      const DistanceData& dist_d = distance.getData();
      const BatteryData& bat_d = battery.getData();

      Serial.println("--- SENSOR DATA ---");
      Serial.print("IMU=ax:");
      Serial.print(imu_d.ax, 3);
      Serial.print(",ay:");
      Serial.print(imu_d.ay, 3);
      Serial.print(",az:");
      Serial.print(imu_d.az, 3);
      Serial.print(",gx:");
      Serial.print(imu_d.gx, 3);
      Serial.print(",gy:");
      Serial.print(imu_d.gy, 3);
      Serial.println(imu_d.gz, 3);

      Serial.print("ENCODER=");
      Serial.print(enc_d.fl); Serial.print(",");
      Serial.print(enc_d.fr); Serial.print(",");
      Serial.print(enc_d.rl); Serial.print(",");
      Serial.println(enc_d.rr);

      Serial.print("FRONT_DISTANCE=");
      Serial.print(dist_d.front_cm, 1);
      Serial.print(",REAR_DISTANCE=");
      Serial.println(dist_d.rear_cm, 1);

      Serial.print("BATTERY=");
      Serial.print(bat_d.voltage, 2);
      Serial.print(",PERCENT=");
      Serial.println(bat_d.percentage, 1);
    }

    else if (line.startsWith("HELP")) {
      Serial.println("Commands: IMU, ENCODER, DISTANCE, BATTERY, ALL, HELP");
    }

    else {
      Serial.println("Unknown command. Type HELP for list.");
    }
  }

  uint32_t now = millis();
  if (now - last_telemetry > 5000) {
    battery.update();
    const BatteryData& d = battery.getData();
    Serial.print("[AUTO] BATTERY=");
    Serial.print(d.voltage, 2);
    Serial.print(",PERCENT=");
    Serial.println(d.percentage, 1);
    last_telemetry = now;
  }
}
