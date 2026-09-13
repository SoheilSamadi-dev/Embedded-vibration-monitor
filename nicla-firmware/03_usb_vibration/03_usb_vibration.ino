#include <Arduino_BHY2.h>
#include "VibrationAccumulator.h"

// Accumulate in the packet callback so multiple packets in one BHY2.update()
// are included, rather than just reading the latest sample once per loop.
class VibrationSensor : public SensorXYZ {
public:
  VibrationSensor() : SensorXYZ(SENSOR_ID_ACC) {}
  VibrationAccumulator vibration;

  void setData(SensorDataPacket &packet) override {
    SensorXYZ::setData(packet);
    vibration.add(x(), y(), z());
  }
};

VibrationSensor accel;
unsigned long lastRaw = 0, lastSummary = 0;

void setup() {
  Serial.begin(115200);
  delay(1500);
  BHY2.begin();
  accel.begin(50);
  lastSummary = millis();
}

void loop() {
  BHY2.update();
  unsigned long now = millis();
  if (now - lastRaw >= 200 && accel.dataAvailable()) {
    lastRaw = now;
    Serial.print("ACC_RAW,"); Serial.print(now); Serial.print(',');
    Serial.print(accel.x()); Serial.print(',');
    Serial.print(accel.y()); Serial.print(','); Serial.println(accel.z());
    accel.clearDataAvailFlag();
  }
  if (now - lastSummary >= 1000) {
    // VIB_RAW,uptime_ms,window_ms,sample_pairs,rms_delta_raw
    Serial.print("VIB_RAW,"); Serial.print(now); Serial.print(',');
    Serial.print(now - lastSummary); Serial.print(',');
    Serial.print(accel.vibration.pairs()); Serial.print(',');
    Serial.println(accel.vibration.rms(), 3);
    accel.vibration.clearWindow();
    lastSummary = now;
  }
}
