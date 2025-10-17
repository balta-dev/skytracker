# SkyTracker - Visualizador Celeste 3D (GRUPO 7)

SkyTracker es una aplicación 3D interactiva para explorar el cielo nocturno y controlar físicamente un Sky Tracker mediante Arduino o ESP32.

Aunque muestra estrellas, planetas, la Luna y galaxias en tiempo real usando Python y Pyglet, su función principal es comunicarle al hardware hacia dónde moverse. 

El usuario puede buscar un objeto celeste mediante el buscador, y el vector en pantalla se moverá automáticamente para apuntarlo; estas coordenadas ```vec_yaw``` y ```vec_pitch``` se envían vía serial al Arduino/ESP32 para mover los servos correspondientes.

El 3D en pantalla sirve como visualización interactiva y control, permitiendo verificar y ajustar el seguimiento sin necesidad de mirar el Sky Tracker físico.

<img width="1271" height="746" alt="image" src="https://github.com/user-attachments/assets/105007b6-24dd-4811-962b-97b8512919e4" />


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
cd SkyTracker
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

## Notas

- Si tenés problemas con dependencias, probá actualizar pip:

```bash
pip install --upgrade pip
```

> **⚠️**: Falta importar ```serial``` para que el simulador pueda enviar los datos a tiempo real a Arduino/ESP32.
> El chip recibiría "yaw" y "pitch" y tendría que mapear ángulos de servo y mover los motores.
