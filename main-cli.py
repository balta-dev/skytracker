import threading
import time
from datetime import datetime, timezone

from celestial_data import get_object_list_text
from astronomy import calculate_lst
from vector import PointerVector
from tracker import ObjectTracker
from config import *
from serial_comm import SerialComm
from server import Server
import sys

class SkyTrackerConsole:
    def __init__(self):
        self.vector = PointerVector()          # Rojo
        self.sensor_vector = PointerVector()   # Verde
        self.tracker = ObjectTracker()
        self.running = True
        self.input_text = ""
        self.current_input = ""
        self.lock = threading.Lock()

        self.server = Server(self)
        self.server.start()

        # Simulación ESP32
        if not SIMULATE:
            self.serial_device = SerialComm(simulate=False)
        else:
            self.serial_device = SerialComm(simulate=True)

    # --- Thread para leer input de manera no bloqueante ---
    def input_thread(self):
        while self.running:
            try:
                c = sys.stdin.read(1)  # lee caracter por caracter
            except Exception:
                continue

            with self.lock:
                if c == "\n":  # Enter
                    self.input_text = self.current_input.strip()
                    self.current_input = ""
                elif c == "\x7f":  # Backspace
                    self.current_input = self.current_input[:-1]
                elif c == "\x1b":  # ESC para cancelar rastreo
                    self.tracker.stop_tracking()
                else:
                    self.current_input += c

    # --- Update de vectores y tracking ---
    def update(self, dt=0.05):
        if self.tracker.is_tracking():
            self.tracker.update_vector_to_target(self.vector)

        # Simula movimiento del vector verde siguiendo al rojo
        follow_speed = 0.1
        self.sensor_vector.yaw += (self.vector.yaw - self.sensor_vector.yaw) * follow_speed
        self.sensor_vector.pitch += (self.vector.pitch - self.sensor_vector.pitch) * follow_speed

    # --- Dibuja consola ---
    def draw_console(self):
        now_utc = datetime.now(timezone.utc)
        lst_deg, lst_h = calculate_lst(now_utc, LOCATION_LONGITUDE)
        tracking_obj = self.tracker.get_tracked_object_name()
        server_ip = self.server.get_server_ip()

        lines = [
            f"VECTOR - Yaw: {self.vector.yaw:.1f}° Pitch: {self.vector.pitch:.1f}°",
            f"FEEDBACK - Yaw: {self.sensor_vector.yaw:.1f}° Pitch: {self.sensor_vector.pitch:.1f}°",
            f"LST: {lst_deg:.2f}° ({lst_h:.2f}h)",
            f"Rastreando: {tracking_obj if tracking_obj else 'ninguno'}",
            "",
            f"SERVIDOR TCP: {server_ip}:12345",
            "",
            "Objetos disponibles:",
            get_object_list_text(),
            "",
            "Escriba el nombre del objeto a rastrear. ESC cancela el rastreo:"
        ]

        # Limpiar pantalla
        print("\033c", end="")
        for line in lines:
            print(line)
        # Mostrar la entrada actual en la última línea
        print(f">>> {self.current_input}", end="", flush=True)

    # --- Manejo de input ---
    def handle_input(self, text):
        if text == "":
            self.tracker.stop_tracking()
        elif self.tracker.start_tracking(text):
            print(f"\nRastreando {text}")
            time.sleep(0.5)
        else:
            print(f"\nNo se encontró el objeto '{text}'")
            time.sleep(1)

    # --- Loop principal ---
    def run(self):
        # Configurar stdin para lectura sin bloqueo
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)

        # Iniciar thread de input
        threading.Thread(target=self.input_thread, daemon=True).start()

        try:
            while self.running:
                self.update()
                self.draw_console()

                # Revisar si hay input
                with self.lock:
                    if self.input_text:
                        self.handle_input(self.input_text)
                        self.input_text = ""

                time.sleep(0.05)
        except KeyboardInterrupt:
            self.running = False
            print("\nSaliendo...")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.server.stop()


if __name__ == "__main__":
    app = SkyTrackerConsole()
    app.run()
