<img width="3840" height="1080" alt="portada" src="https://github.com/user-attachments/assets/ea6b2675-51a8-4f3e-9421-b3312a69295e" />

---

# GRUPO 7 - Sistema de seguimiento estelar a tiempo real

### ¿Qué es "SkyTracker"? ¿Seguimiento estelar?
SkyTracker es un proyecto interactivo presentado para la cátedra "Tecnologías para la Automatización" en la UTN FRCU por el grupo 7. Permite localización de planetas, estrellas y galaxias a través de una interfaz comunicada con un ESP32. No sólamente es un sandbox 3D hecho en Python y OpenGL (Pyglet): su función principal es permitir la comunicación bilateral entre el localizador físico y tu dispositivo móvil.

<img width="1920" height="1048" alt="image" src="https://github.com/user-attachments/assets/9c6f4c1d-2989-4a77-bd2e-73b4f93275e1" />

<img width="400" height="929" alt="image" src="https://github.com/user-attachments/assets/7e3ac4bd-338f-46d9-99aa-fb89cd044a7f" />
<img width="400" height="745" alt="image" src="https://github.com/user-attachments/assets/9a25cc7b-eaa0-4959-af3b-731407be0639" />

---

El usuario puede buscar un objeto celeste mediante el buscador (PC/Android), y el vector *rojo* (TARGET) en pantalla se moverá automáticamente para apuntarlo; estas coordenadas ```vec_yaw``` y ```vec_pitch``` se envían vía serial al ESP32 para 
mover los servos correspondientes. El vector *verde* corresponde al FEEDBACK (retroalimentación) de los sensores para comparar posiciones, compensar y ajustar, etcétera. 

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/14de4f69-648c-408a-b4d3-2b10ab065a77" />
<img width="1920" height="1053" alt="image" src="https://github.com/user-attachments/assets/ce78b566-bbfc-42bc-a5a4-1ebeb8598768" />

---

No es obligatorio utilizar la interfaz gráfica, también existe una versión de consola ```main-cli.py``` para ahorrar batería y recursos del sistema.

<img width="1157" height="339" alt="image" src="https://github.com/user-attachments/assets/daba160d-4552-4ac7-9e75-77703e51fb07" />


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
cd python/skytracker
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

> **⚠️ Nota**: Es recomendable ejecutar ```/shared/calculations/ephemeris_calculator.py``` periódicamente para mantener actualizados los objetos celestiales en el cielo, sobre todo la Luna y los planetas.

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
