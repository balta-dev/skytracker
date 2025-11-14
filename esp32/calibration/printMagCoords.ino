/*
Salida CSV de lecturas del magnetómetro (X, Y, Z)
Adaptado para ESP32 + MPU9250 usando la librería MPU9250_asukiaaa.

Este código es una implementación propia, inspirada en el procedimiento
explicado por Michael Wrona (mag-cal-example), pero sin reutilizar código
del repositorio original.
*/

#include <Wire.h>
#include <MPU9250_asukiaaa.h>

MPU9250_asukiaaa mySensor;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); // SDA = 21, SCL = 22 por defecto en ESP32

  mySensor.setWire(&Wire);
  mySensor.beginAccel();
  mySensor.beginGyro();
  mySensor.beginMag();

  Serial.println("MPU9250 Magnetometer CSV Output");
  delay(500);
}

void loop() {
  mySensor.accelUpdate();
  mySensor.gyroUpdate();
  mySensor.magUpdate();

  // Salida CSV: X, Y, Z
  Serial.print(mySensor.magX());
  Serial.print(",");
  Serial.print(mySensor.magY());
  Serial.print(",");
  Serial.println(mySensor.magZ());

  delay(100); // 10 Hz
}
