# SkyTracker – Guía rápida para Python

Este directorio contiene **todo lo necesario para utilizar Python como cerebro o intermediario** a tu ESP32.

---

## Requisitos

- Python 3.10 o superior  
- Soporte OpenGL en la máquina  
- Dependencias listadas en `requirements.txt` (por ejemplo: `pyglet`)

---

## Clonar el repositorio

```bash
git clone https://github.com/balta-dev/skytracker.git
cd python/
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

> **Nota**: no es obligatorio utilizar la interfaz gráfica, también existe una versión de consola ```main-cli.py``` para ahorrar batería y recursos del sistema.
>
> **Nota 2:** si eres un usuario de Windows y te da problemas al arrancar el programa, ejecuta los siguientes comandos:
>
> ```bash pip uninstall -y pyglet
> pip uninstall -y pyglet
> pip install "pyglet<2.0"
> python3 main.py
> ```

---

## Controles por defecto

La clase `InputHandler` procesa entrada de teclado para:

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

## Servidor TCP/IP

Automáticamente al iniciar, Python genera un servidor TCP/IP al que puedes conectarte a través de tu teléfono. Esto es opcional y sólo está pensado para ocuparse en conjunto con la app de Android como otro modo más de operación. Para más detalle, lea el ```README.md``` en la carpeta raíz. 