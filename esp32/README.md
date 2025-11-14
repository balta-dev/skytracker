# SkyTracker – Guía rápida para el hardware

Este directorio contiene **todo lo necesario para construir y calibrar el SkyTracker**:  
archivos CAD imprimibles, firmware listo para flashear y herramientas de calibración del sensor.

---

## Contenido

### **1. `/CAD/` – Archivos 3D imprimibles**
En esta carpeta vas a encontrar todos los **modelos `.stl`** necesarios para imprimir la montura completa:

- ```tripod_mount.stl``` – Base para trípode  
- ```base.stl``` – Estructura principal  
- ```base_screw.stl``` – Tornillo de fijación, ideal para testing (x3)
- ```base_gear_small.stl / base_gear_big.stl``` – Engranajes de la base  
- ```first_gear_DEC.stl / second_gear_DEC.stl / small_gear_DEC.stl``` – Engranajes del eje DEC  
- ```DEC_mount.stl``` – Montura del eje DEC  
- ```gyro_mount.stl``` – Soporte para IMU  
- ```laser_mount.stl``` – Soporte para láser de alineación  

Todos los modelos están listos para slicing e impresión sin modificaciones.

---

### **2. `/calibration/` – Utilidades de calibración**
Incluye herramientas para dejar el sensor correctamente calibrado antes de usar el sistema:

- ```printMagCoords.ino``` – Sketch para leer datos crudos del magnetómetro y graficarlos en PC.  
  Esto te permite obtener los offsets y escala necesarios para una correcta orientación absoluta.
  
  > Nota: Es necesario descargar [log-mag-readings.py](https://github.com/michaelwro/mag-cal-example/), hecho por Michael Wrona. Este software crea un documento de texto de puntos para calibrar el magnetómetro con [Magneto Copyright (C) 2013](https://sites.google.com/view/sailboatinstruments1).

---

### **3. `firmware.ino` – Código principal del SkyTracker**
Es el firmware que se flashea directamente en el ESP32.

Este archivo incluye:
- Lectura continua del IMU  
- Fusión de sensores (orientación)  
- Control del eje  
- Comunicación por serie y TCP  
- Soporte para comandos desde PC  
- Lógica de seguimiento  

Puedes compilarlo con Arduino IDE.

---

## Uso

1. **Imprimir las piezas CAD**.
2. **Seguir la guía** de [Görkem Bozkurt](https://gorkem.cc/projects/StarTrack/) para ensamblar la estructura mecánica completa.  
3. **Flashear temporalmente** con el sketch de calibración `printMagCoords.ino`.  
4. **Descargar y ejecutar** [```log-mag-readings.py```](https://github.com/michaelwro/mag-cal-example/blob/main/log-mag-readings.py). Cuando lo ejecutes realice movimientos amplios en todas direcciones. [Click aquí](https://youtube.com/shorts/R1hDZUb_1ec?si=I-tqwduHXR1qzCST) para ver un ejemplo.
5. **Descargar y descomprimir** [```magneto12.zip```](https://drive.google.com/file/d/1xFDOOaQSMza8PcDdrJCcDIvW02Dkvv9k/view) y ejecutar Magneto. Cargar el archivo ```mag-readings.txt``` y darle a "Calibrate".
6. **Actualizar** en `firmware.ino` los valores de calibración (bias y matriz de escala) obtenidos con Magneto, ya que cada IMU tiene parámetros distintos.  Si no sabes qué cambiar, por favor revisa el directorio ```/docs/images/```.
7. **Flashear el firmware** a tu ESP32 con `firmware.ino`.  
8. ¡Comenzar a usar el SkyTracker!

---

## Configuración del Hardware

El firmware del ESP32 espera la siguiente configuración de pines:

| Componente                          | Pin  | Propósito                                                    |
| ----------------------------------- | ---- | ------------------------------------------------------------ |
| LCD I2C (SDA)                       | 21   | Bus I2C compartido con MPU9250 y LCD 16x2 (dirección 0x27)   |
| LCD I2C (SCL)                       | 22   | Bus I2C compartido con MPU9250 y LCD 16x2                    |
| LCD I2C (VCC)                       | 5V   | Alimentación del módulo LCD (5V)                             |
| LCD I2C (GND)                       | GND  | Tierra común con ESP32                                       |
| MPU9250 (SDA)                       | 21   | Sensor 9-DOF: única fuente de feedback real (yaw, pitch, roll) |
| MPU9250 (SCL)                       | 22   | Sensor 9-DOF: mide orientación actual del sistema            |
| MPU9250 (VCC)                       | 3V3  | Alimentación del sensor 9DOF (3.3V)                          |
| MPU9250 (AD0)                       | GND  | Dirección I2C = 0x68 (conectado a GND)                       |
| MPU9250 (GND)                       | GND  | Tierra común con ESP32                                       |
| Servo SG90 Yaw (señal de control)   | 18   | Control del servo de azimut (base giratoria) – solo salida PWM |
| Servo SG90 Yaw (VCC)                | 5V   | Alimentación del servo                                       |
| Servo SG90 Yaw (GND)                | GND  | Tierra común con ESP32                                       |
| Servo SG90 Pitch (señal de control) | 19   | Control del servo de elevación (brazo vertical) – solo salida PWM |
| Servo SG90 Pitch (VCC)              | 5V   | Alimentación del servo                                       |
| Servo SG90 Pitch (GND)              | GND  | Tierra común con ESP32                                       |

<img src="../docs/scheme/Diagrama de conexión.png"></img>

> Nota: es **muy importante** que todos estén en el mismo GND del ESP32. 

## Notas finales

Este proyecto está pensado para ser modular, fácil de adaptar y sencillo de entender.  
Podés cambiar engranajes, utilizar distintos sensores o modificar la electrónica sin inconvenientes.

Si necesitás editar alguna pieza, podés actualizar o rehacer los archivos CAD a partir de los modelos originales disponibles en el  blog de Görkem Bozkurt: https://gorkem.cc/projects/StarTrack/

Y si querés sumar alguna mejora o corrección, ¡sentite libre de abrir un PR!
