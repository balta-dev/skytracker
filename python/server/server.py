# server.py
"""
Servidor TCP con soporte para tracking y datos en tiempo real.
- Cliente envía: "objeto\n" → Servidor responde "OK\n" y empieza a enviar "DATA:yaw,pitch\n" y "SENSOR:yaw,pitch\n" cada 100ms.
- Cliente envía: "stop\n" → Para tracking y cierra conexión.
- Protocolo: Líneas terminadas en \n.
"""

import socket
import threading
import time
from shared.celestial_data import get_all_celestial_objects


class Server:
    def __init__(self, app, host='0.0.0.0', port=12345, backlog=5, update_interval=0.1):
        self.app = app
        self.host = host
        self.port = port
        self.backlog = backlog
        self.update_interval = update_interval  # Segundos entre updates (0.1 = 100ms)
        self.server_socket = None
        self.running = False
        self.thread = None
        self.valid_objects = get_all_celestial_objects()
        self.clients = []  # Lista de clients activos (socket, writer)
        self.server_ip = self._get_local_ip()

    def _get_local_ip(self):
        """Obtiene la IP local del servidor sin depender de comandos del SO"""
        try:
            # Truco: conectar a un servidor externo para obtener la IP local
            # No envía datos, solo obtiene la IP de la interfaz que se usaría
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_server_ip(self):
        """Retorna la IP del servidor"""
        return self.server_ip

    def start(self):
        if self.running:
            print("[Server] Ya está corriendo")
            return
        self.running = True
        self.thread = threading.Thread(target=self._server_loop, daemon=True)
        self.thread.start()
        print(f"[Server] Iniciado en {self.server_ip}:{self.port} (updates cada {self.update_interval*1000}ms)")

    def stop(self):
        if not self.running:
            return
        self.running = False
        for client in self.clients:
            try:
                client[1].close()  # Cerrar writer
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        if self.thread:
            self.thread.join(timeout=5.0)
        print("[Server] Detenido")

    def _server_loop(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.backlog)
            self.server_socket.settimeout(1.0)

            print(f"[Server] Escuchando en {self.host}:{self.port}")
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"[Server] Nueva conexión desde {addr}")
                    threading.Thread(target=self._handle_client, args=(client_socket, addr), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[Server] Error aceptando: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"[Server] Error iniciando: {e}")
        finally:
            self.running = False

    def _handle_client(self, client_socket, addr):
        writer = None
        try:
            client_socket.settimeout(10.0)
            reader = client_socket.makefile('r', encoding='utf-8')
            writer = client_socket.makefile('w', encoding='utf-8')
            writer = PrintWriter(client_socket, True)  # Para auto-flush

            while self.running:
                line = reader.readline().strip()
                if not line:
                    break

                if line.lower() == "stop":
                    self.app.tracker.stop_tracking()
                    writer.write("STOPPED\n")
                    break

                obj_name = line.lower()
                print(f"[Server] {addr}: Tracking '{obj_name}'")

                if obj_name not in self.valid_objects:
                    writer.write(f"ERROR: Objeto '{obj_name}' no encontrado\n")
                    continue

                success = self.app.tracker.start_tracking(obj_name.capitalize())
                if success:
                    writer.write("OK\n")
                    # Agregar a clients para updates
                    self.clients.append((client_socket, writer))
                    # Thread para enviar datos en tiempo real
                    threading.Thread(target=self._send_realtime_data, args=(client_socket, addr), daemon=True).start()
                else:
                    writer.write("ERROR: No se pudo iniciar rastreo\n")

        except Exception as e:
            print(f"[Server] {addr}: Error: {e}")
        finally:
            if writer:
                writer.close()
            client_socket.close()
            if client_socket in [c[0] for c in self.clients]:
                self.clients = [c for c in self.clients if c[0] != client_socket]

    def _send_realtime_data(self, client_socket, addr):
        """Envía yaw/pitch del vector y del sensor cada update_interval"""
        while self.running and client_socket.fileno() != -1:
            try:
                # Vector comandado (target)
                yaw = self.app.vector.yaw
                pitch = self.app.vector.pitch
                data = f"DATA:{yaw:.1f},{pitch:.1f}\n"
                client_socket.send(data.encode('utf-8'))
                
                # Sensor feedback (real)
                sensor_yaw = self.app.sensor_vector.yaw
                sensor_pitch = self.app.sensor_vector.pitch
                sensor_data = f"SENSOR:{sensor_yaw:.1f},{sensor_pitch:.1f}\n"
                client_socket.send(sensor_data.encode('utf-8'))
                
                time.sleep(self.update_interval)
            except:
                break

class PrintWriter:
    def __init__(self, socket, auto_flush=True):
        self.socket = socket
        self.auto_flush = auto_flush

    def write(self, s):
        self.socket.sendall(s.encode('utf-8'))
        if self.auto_flush and s.endswith('\n'):
            pass  # sendall ya envía todo

    def flush(self):
        pass

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_WR)
        except:
            pass