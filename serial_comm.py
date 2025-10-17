# serial_comm.py
"""
Comunicación Serial para enviar yaw/pitch a Arduino/ESP32
"""

import serial
import time
import sys

class SerialComm:
    """Clase para manejar la comunicación serial"""
    
    def __init__(self, port=None, baudrate=115200, simulate=False, max_hz=50):
        """
        Args:
            port (str): Puerto serial (ej: '/dev/ttyUSB0' o 'COM3')
            baudrate (int): Baud rate de la placa
            simulate (bool): Si True, no usa hardware real y solo imprime
        """
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
                self.ser = serial.Serial(port, baudrate, timeout=1)
                time.sleep(2)  # espera reset de Arduino/ESP32
                print(f"[Serial] Conectado a {port} a {baudrate} baudios")
            except serial.SerialException as e:
                print(f"[Serial] Error al abrir puerto {port}: {e}")
                sys.exit(1)
        else:
            print("[Serial] Modo simulación activado")
    
    def send_angles(self, yaw, pitch):
        
        """Envía yaw/pitch solo si cambiaron y respetando frecuencia máxima"""
        now = time.time()

        # Limitar frecuencia
        if now - self.last_time < self.min_interval:
            return

        # Enviar solo si hay cambio
        if self.last_yaw == yaw and self.last_pitch == pitch:
            return

        self.last_yaw = yaw
        self.last_pitch = pitch
        self.last_time = now

        """
        Envía yaw y pitch separados por coma, terminando en newline.
        Ej: "123.45,67.89\n"
        """
        message = f"{yaw:.2f},{pitch:.2f}\n"
        if self.simulate:
            print(f"[Simulación] Enviando: {message.strip()}")
        else:
            try:
                self.ser.write(message.encode('utf-8'))
            except serial.SerialException as e:
                print(f"[Serial] Error al enviar: {e}")
    
    def close(self):
        """Cierra el puerto serial"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[Serial] Puerto {self.port} cerrado")
