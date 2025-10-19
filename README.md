# SkyTracker - Visualizador Celeste 3D (GRUPO 7)

SkyTracker es una aplicación 3D interactiva para explorar el cielo nocturno y controlar físicamente un Sky Tracker mediante Arduino o ESP32.

Aunque muestra estrellas, planetas, la Luna y galaxias en tiempo real usando Python y Pyglet, su función principal es comunicarle al hardware hacia dónde moverse. 

El usuario puede buscar un objeto celeste mediante el buscador, y el vector en pantalla se moverá automáticamente para apuntarlo; estas coordenadas ```vec_yaw``` y ```vec_pitch``` se envían vía serial al Arduino/ESP32 para mover los servos correspondientes.

El 3D en pantalla sirve como visualización interactiva y control, permitiendo verificar y ajustar el seguimiento sin necesidad de mirar el Sky Tracker físico.

---

<img width="1271" height="746" alt="image" src="https://github.com/user-attachments/assets/105007b6-24dd-4811-962b-97b8512919e4" />

---
Simulación con Potenciómetros en Tinkercad:
[<img width="1657" height="909" alt="image" src="https://github.com/user-attachments/assets/558280fc-9322-458c-a0b2-35c1ace515cb" />](https://www.tinkercad.com/things/3lo1FGcupPU-skytracker-grupo-7-simulacion)

Vista Esquemática:
[<img width="1078" height="839" alt="image" src="https://github.com/user-attachments/assets/a4cf48fa-da64-44cc-9320-9ed436780206" />](https://www.tinkercad.com/things/3lo1FGcupPU-skytracker-grupo-7-simulacion)

```c++
#include <Servo.h>

Servo servoYaw;
Servo servoPitch;

// Pines
const int potTargetYawPin   = A0;
const int potTargetPitchPin = A1;
const int potFeedbackYawPin   = A2; // simula MPU
const int potFeedbackPitchPin = A3; // simula MPU
const int potRollPin          = A4; // roll simulado

// Parámetros de control
const float Kp = 0.5;        // Factor proporcional
const float rollFactorYaw = 0.3;
const float rollFactorPitch = 0.2;

void setup() {
  servoYaw.attach(9);
  servoPitch.attach(10);
  Serial.begin(9600);
}

void loop() {
  // --- Leer targets ---
  int targetYawRaw   = analogRead(potTargetYawPin);
  int targetPitchRaw = analogRead(potTargetPitchPin);

  float targetYaw   = map(targetYawRaw,   0, 1023, 0, 180);
  float targetPitch = map(targetPitchRaw, 0, 1023, 0, 180);

  // --- Leer feedback ---
  int feedbackYawRaw   = analogRead(potFeedbackYawPin);
  int feedbackPitchRaw = analogRead(potFeedbackPitchPin);
  int feedbackRollRaw  = analogRead(potRollPin);

  float feedbackYaw   = map(feedbackYawRaw,   0, 1023, 0, 180);
  float feedbackPitch = map(feedbackPitchRaw, 0, 1023, 0, 180);
  float feedbackRoll  = map(feedbackRollRaw,  0, 1023, 0, 180);

  // --- Calcular errores ---
  float errorYaw   = targetYaw - feedbackYaw;
  float errorPitch = targetPitch - feedbackPitch;

  // --- Calcular offsets por roll ---
  float rollOffsetYaw   = (feedbackRoll - 90) * rollFactorYaw;
  float rollOffsetPitch = (feedbackRoll - 90) * rollFactorPitch;

  // --- Calcular posiciones finales para el servo ---
  float servoYawPos   = feedbackYaw + errorYaw * Kp + rollOffsetYaw;
  float servoPitchPos = feedbackPitch + errorPitch * Kp + rollOffsetPitch;

  // --- Limitar rangos ---
  servoYawPos   = constrain(servoYawPos,   0, 180);
  servoPitchPos = constrain(servoPitchPos, 0, 180);

  // --- Mover servos ---
  servoYaw.write(servoYawPos);
  servoPitch.write(servoPitchPos);

  // --- Debug ---
  Serial.print("Target Yaw: "); Serial.print(targetYaw);
  Serial.print(" | Feedback Yaw: "); Serial.print(feedbackYaw);
  Serial.print(" | Servo Yaw: "); Serial.println(servoYawPos);

  Serial.print("Target Pitch: "); Serial.print(targetPitch);
  Serial.print(" | Feedback Pitch: "); Serial.print(feedbackPitch);
  Serial.print(" | Servo Pitch: "); Serial.println(servoPitchPos);

  Serial.print("Feedback Roll: "); Serial.println(feedbackRoll);
  Serial.println("----------------------");

  delay(50);
}
```

---
Basado en la idea de Görkem Bozkurt:
[![1](https://content.instructables.com/F7M/RLBH/IR40FE1K/F7MRLBHIR40FE1K.jpg)](https://vimeo.com/176745067)
[![2](https://github.com/user-attachments/assets/5283ce86-9bf0-4b3a-b41c-35084c5242c9)](https://vimeo.com/176745067)

---

## Requisitos

- Python 3.10 o superior  
- Soporte OpenGL en la máquina  
- Dependencias listadas en `requirements.txt` (por ejemplo: `pyglet`)

---

## Clonar el repositorio

```bash
git clone https://github.com/balta-dev/skytracker.git
cd skytracker
```

---

## Crear y activar entorno virtual

Crear el entorno:

```bash
python -m venv .venv
```

Activar el entorno:

- En Linux / macOS:

```bash
source .venv/bin/activate
```

- En Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

---

## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecutar la aplicación

Con el entorno virtual activado:

```bash
python3 main.py
```

> **⚠️ Nota**: Es recomendable ejecutar ```ephemeris_calculator.py``` periódicamente para mantener actualizados los objetos celestiales en el cielo, sobre todo la Luna y los planetas.

---

## Controles por defecto

- `W/A/S/D` — mover cámara en el plano horizontal  
- `Space` — subir cámara  
- `Shift` — bajar cámara  
- Mouse — rotar cámara  
- `Z` / `X` — acercar / alejar (FOV)  
- Flechas — mover vector de apuntado  
- `T` — abrir cuadro de búsqueda  
- `ENTER` — confirmar búsqueda  
- `ESC` — cancelar búsqueda / cerrar cuadro  
- `C` — cancelar seguimiento

---
