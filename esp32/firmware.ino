#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <MPU9250_asukiaaa.h>

// ================= CONFIGURACIÓN =================
const char* ssid     = "NombreDeRed";
const char* password = "Contraseña";
const uint16_t PORT  = 12345;

// LCD 16x2 I2C
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Sensor
MPU9250_asukiaaa mySensor;

// TCP
WiFiServer server(PORT);
WiFiClient client;

// Estado actual del sensor (actualizado continuamente)
float current_yaw = 0.0;
float current_pitch = 0.0;
float current_roll = 0.0;

// Últimos mensajes
String lastCMD = "N/A";
String lastSND = "N/A";

// Timing para actualización continua
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 20; // 50Hz

// ================= VALORES DE CALIBRACIÓN (Magneto 1.2) =================
float magBias[3] = {34.720527, 108.115537, -78.666122};

float magScale[3][3] = {
  { 1.513097, 0.052649,  -0.019279},
  { 0.052649,  0.608112, 0.249034},
  { -0.019279, 0.249034,  1.469883}
};

// ================= FILTRO COMPLEMENTARIO SIMPLE =================
const float alpha = 0.98; // 98% gyro, 2% accel/mag
unsigned long lastFilterUpdate = 0;

// ================= FUNCIONES LCD =================
void updateLCD(String line0, String line1) {
  lcd.setCursor(0, 0);
  lcd.print("                ");
  lcd.setCursor(0, 0);
  lcd.print(line0.substring(0, 16));

  lcd.setCursor(0, 1);
  lcd.print("                ");
  lcd.setCursor(0, 1);
  lcd.print(line1.substring(0, 16));
}

void showWaitingCMD() {
  lcd.setCursor(0, 0);
  lcd.print("Esperando CMD   ");
  lcd.setCursor(0, 1);
  lcd.print("IP:");
  lcd.print(WiFi.localIP());
}

// ================= ACTUALIZACIÓN CONTINUA DE SENSORES =================
void updateSensorsContinuous() {
  unsigned long now = millis();
  
  // Actualizar cada UPDATE_INTERVAL ms
  if (now - lastUpdate < UPDATE_INTERVAL) {
    return;
  }
  
  // Calcular dt
  float dt = (now - lastFilterUpdate) / 1000.0;
  lastFilterUpdate = now;
  lastUpdate = now;
  
  if (dt > 1.0) dt = 0.02; // Protección primera iteración

  // Leer acelerómetro, giroscopio y magnetómetro
  if (mySensor.accelUpdate() == 0 && 
      mySensor.gyroUpdate() == 0 && 
      mySensor.magUpdate() == 0) {

    // ---- ACELERÓMETRO (referencia de gravedad) ----
    float ax = mySensor.accelX();
    float ay = mySensor.accelY();
    float az = mySensor.accelZ();

    float accel_pitch = -atan2(-ay, sqrt(ax*ax + az*az)) * 180.0 / PI;
    float accel_roll  = atan2(ax, az) * 180.0 / PI;

    // ---- GIROSCOPIO (velocidad angular en deg/s) ----
    float gx = mySensor.gyroX();
    float gy = mySensor.gyroY();
    float gz = mySensor.gyroZ();

    // Integrar giroscopio
    float gyro_pitch = current_pitch + gy * dt;
    float gyro_roll  = current_roll  + gx * dt;
    float gyro_yaw   = current_yaw   + gz * dt;

    // ---- FILTRO COMPLEMENTARIO ----
    current_pitch = alpha * gyro_pitch + (1.0 - alpha) * accel_pitch;
    current_roll  = alpha * gyro_roll  + (1.0 - alpha) * accel_roll;

    // ---- MAGNETÓMETRO (yaw con compensación de tilt) ----
    float mx_raw = mySensor.magX();
    float my_raw = mySensor.magY();
    float mz_raw = mySensor.magZ();

    // Calibración hard-iron
    float mx = mx_raw - magBias[0];
    float my = my_raw - magBias[1];
    float mz = mz_raw - magBias[2];

    // Calibración soft-iron
    float mx_cal = magScale[0][0]*mx + magScale[0][1]*my + magScale[0][2]*mz;
    float my_cal = magScale[1][0]*mx + magScale[1][1]*my + magScale[1][2]*mz;
    float mz_cal = magScale[2][0]*mx + magScale[2][1]*my + magScale[2][2]*mz;

    // Compensación de tilt
    float cosR = cos(current_roll  * PI / 180.0);
    float sinR = sin(current_roll  * PI / 180.0);
    float cosP = cos(current_pitch * PI / 180.0);
    float sinP = sin(current_pitch * PI / 180.0);

    float Xh = mx_cal * cosP + mz_cal * sinP;
    float Yh = mx_cal * sinR * sinP + my_cal * cosR - mz_cal * sinR * cosP;

    float mag_yaw = atan2(-Yh, Xh) * 180.0 / PI;
    if (mag_yaw < 0) mag_yaw += 360.0;

    // Fusionar yaw (corregir drift del gyro con magnetómetro)
    float yaw_diff = mag_yaw - current_yaw;
    if (yaw_diff > 180) yaw_diff -= 360;
    if (yaw_diff < -180) yaw_diff += 360;
    
    current_yaw = gyro_yaw + (1.0 - alpha) * yaw_diff;
    
    // Normalizar yaw
    while (current_yaw < 0) current_yaw += 360.0;
    while (current_yaw >= 360) current_yaw -= 360.0;
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  Wire.begin();

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.print("Encendiendo...");
  delay(1000);

  // ---------- MPU9250 ----------
  lcd.setCursor(0, 0);
  lcd.print("Iniciando sensor");
  mySensor.setWire(&Wire);
  mySensor.beginAccel();
  mySensor.beginGyro();
  mySensor.beginMag();
  Serial.println("MPU9250 OK");

  // ---------- WiFi ----------
  lcd.setCursor(0, 0);
  lcd.print("Conectando WiFi ");
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    server.begin();
    
    lcd.setCursor(0, 0);
    lcd.print("Sensor activo   ");
    lcd.setCursor(0, 1);
    lcd.print("IP:");
    lcd.print(WiFi.localIP());
  } else {
    lcd.setCursor(0, 0);
    lcd.print("WiFi ERROR!     ");
    Serial.println("WiFi fallo");
  }

  lastUpdate = millis();
  lastFilterUpdate = millis();
}

// ================= LOOP =================
void loop() {
  // ========================================
  // ACTUALIZAR SENSORES CONTINUAMENTE
  // ========================================
  updateSensorsContinuous();

  // ========================================
  // GESTIÓN CLIENTE TCP
  // ========================================
  if (!client.connected()) {
    client = server.available();
    if (client && client.connected()) {
      Serial.println("Cliente conectado");
    }
  }

  // ========================================
  // LEER COMANDOS
  // ========================================
  String cmdInput = "";
  
  if (Serial.available()) {
    cmdInput = Serial.readStringUntil('\n');
    cmdInput.trim();
  }
  
  if (client.connected() && client.available()) {
    String tcp = client.readStringUntil('\n');
    tcp.trim();
    if (tcp.length() > 0) {
      cmdInput = tcp;
    }
  }

  // ========================================
  // RESPONDER
  // ========================================
  if (cmdInput.startsWith("CMD:")) {
    lastCMD = cmdInput;

    // Responder con estado ACTUAL del sensor
    lastSND = "SENS:" + String(current_yaw, 1) + "," + String(current_pitch, 1);
   
    Serial.println(lastSND);
    if (client.connected()) {
      client.println(lastSND);
    }

    updateLCD(lastCMD, lastSND);
  }

  delay(1);
}