# serial_comm.py
"""
Comunicación Serial bidireccional con ESP32.
Soporta envío de comandos (CMD) y lectura de sensores (SENS).
"""

import serial
import time
import sys

class SerialComm:
    """Clase para manejar la comunicación serial"""

    def __init__(self, port=None, baudrate=115200, simulate=False, max_hz=50):
        self.simulate = simulate
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.last_yaw = None
        self.last_pitch = None
        self.last_time = 0.0
        self.min_interval = 1.0 / max_hz  # segundos entre envíos

        if not simulate:
            if port is None:
                raise ValueError("Debes especificar el puerto serial si no es simulación")
            try:
                self.ser = serial.Serial(port, baudrate, timeout=0.1)
                time.sleep(2)  # Espera a que el ESP32 se reinicie
                print(f"[Serial] Conectado a {port} a {baudrate} baudios")
            except serial.SerialException as e:
                print(f"[Serial] Error al abrir puerto {port}: {e}")
                sys.exit(1)
        else:
            print("[Serial] Modo simulación activado")

    # ===========================
    # ENVÍO DE COMANDOS
    # ===========================
    def send_angles(self, yaw, pitch):
        """Envía yaw/pitch como comando CMD solo si cambió y respetando la frecuencia máxima"""
        now = time.time()

        if now - self.last_time < self.min_interval:
            return

        if self.last_yaw == yaw and self.last_pitch == pitch:
            return

        self.last_yaw = yaw
        self.last_pitch = pitch
        self.last_time = now

        message = f"CMD:{yaw:.2f},{pitch:.2f}\n"
        if self.simulate:
            print(f"[Simulación ➝ ESP32] {message.strip()}")
        else:
            try:
                self.ser.write(message.encode('utf-8'))
            except serial.SerialException as e:
                print(f"[Serial] Error al enviar: {e}")

    # ===========================
    # LECTURA DE DATOS
    # ===========================
    def read_data(self):
        """
        Lee una línea del ESP32.
        Espera mensajes tipo:
        - SENS:valor1,valor2
        - STAT:algo
        - ERR:mensaje
        """
        if self.simulate:
            # Podés simular una respuesta de sensor para debug
            return "SENS:0.00,0.00"

        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    return line
            except serial.SerialException as e:
                print(f"[Serial] Error al leer: {e}")
        return None

    def parse_message(self, line):
        """
        Parsea mensajes en formato:
        - 'SENS:yaw,pitch'
        Devuelve un diccionario con tipo y datos.
        """
        if not line:
            return None

        if line.startswith("SENS:"):
            try:
                vals = line[5:].split(",")
                yaw = float(vals[0])
                pitch = float(vals[1])
                return {"type": "SENS", "yaw": yaw, "pitch": pitch}
            except (ValueError, IndexError):
                return {"type": "ERROR", "raw": line}

        # Otros tipos de mensaje podrían manejarse aquí:
        # if line.startswith("STAT:") ...
        # if line.startswith("ERR:") ...

        return {"type": "UNKNOWN", "raw": line}

    # ===========================
    # 🔚 CIERRE
    # ===========================
    def close(self):
        """Cierra el puerto serial"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[Serial] Puerto {self.port} cerrado")
