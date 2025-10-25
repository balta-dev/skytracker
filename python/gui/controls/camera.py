# camera.py
"""
Gestión de la cámara y controles
"""
import math
from pyglet.gl import *
from config import (
    CAM_X, CAM_Y, CAM_Z, CAM_YAW, CAM_PITCH,
    CAM_SPEED_BASE, MOUSE_SENSITIVITY_BASE, FOV
)


class Camera:
    """Clase para gestionar la cámara del usuario"""
    
    def __init__(self):
        self.x = CAM_X
        self.y = CAM_Y
        self.z = CAM_Z
        self.yaw = CAM_YAW
        self.pitch = CAM_PITCH
        self.speed_base = CAM_SPEED_BASE
        self.speed = CAM_SPEED_BASE
        self.sensitivity_base = MOUSE_SENSITIVITY_BASE
        self.sensitivity = MOUSE_SENSITIVITY_BASE
        self.fov = FOV
        self._first_mouse_event = True

        # Caché de la dirección de la cámara
        self._dir_x, self._dir_y, self._dir_z = self.get_direction()
        # Caché del coseno del FOV/2
        self._cos_fov_half = math.cos(math.radians(self.fov * 1.65 / 2))

        # Deadzone para eliminar drift en movimientos pequeños
        self.mouse_deadzone = 0.1

        # Compensación de bias sistemático (ajusta estos valores)
        self.drift_compensation_x = 0.42  # Compensa drift hacia izquierda
        self.drift_compensation_y = -0.42  # Compensa drift hacia arriba
    
    def apply_view(self):
        """Aplica la transformación de la cámara"""
        glLoadIdentity()
        dx, dy, dz = self.get_direction()
        gluLookAt(
            self.x, self.y, self.z,
            self.x + dx, self.y + dy, self.z + dz,
            0, 1, 0
        )
    
    def get_direction(self):
        """Retorna el vector de dirección de la cámara"""
        dx = math.cos(math.radians(self.pitch)) * math.sin(math.radians(self.yaw))
        dy = math.sin(math.radians(self.pitch))
        dz = -math.cos(math.radians(self.pitch)) * math.cos(math.radians(self.yaw))
        return dx, dy, dz

    def is_in_view(self, obj_pos, fov_deg, max_distance=200.0):
        """Determina si un punto está dentro del campo de visión"""
        # Vector cámara → objeto
        dx = obj_pos[0] - self.x
        dy = obj_pos[1] - self.y
        dz = obj_pos[2] - self.z

        # Verificar distancia (usando distancia al cuadrado)
        dist_sq = dx*dx + dy*dy + dz*dz
        max_dist_sq = max_distance * max_distance
        if dist_sq > max_dist_sq:
            return False

        # Calcular producto escalar sin normalización explícita
        distance = math.sqrt(dist_sq)  # Solo necesitamos sqrt si pasamos la verificación de distancia
        dot = (self._dir_x * dx + self._dir_y * dy + self._dir_z * dz) / distance

        # Comparar con el coseno del ángulo FOV/2
        return dot >= self._cos_fov_half
    
    def rotate(self, dx, dy):
        """Rota la cámara según el movimiento del mouse"""
        
        if self._first_mouse_event:
            self._first_mouse_event = False
            return

        # Aplicar compensación de bias sistemático ANTES del deadzone
        dx += self.drift_compensation_x
        dy += self.drift_compensation_y

        # Aplicar deadzone para eliminar micro-drift
        if abs(dx) < self.mouse_deadzone:
            dx = 0
        if abs(dy) < self.mouse_deadzone:
            dy = 0
        
        # Si no hay movimiento significativo, salir
        if dx == 0 and dy == 0:
            return
        
        self.yaw += dx * self.sensitivity
        self.pitch += dy * self.sensitivity
        self.pitch = max(min(self.pitch, 89), -89)
        self.yaw %= 360

        # Actualizar dirección de la cámara
        self._dir_x, self._dir_y, self._dir_z = self.get_direction()
    
    def move_forward(self, amount):
        """Mueve la cámara hacia adelante"""
        fx = math.sin(math.radians(self.yaw))
        fz = -math.cos(math.radians(self.yaw))
        self.x += fx * amount
        self.z += fz * amount
    
    def move_backward(self, amount):
        """Mueve la cámara hacia atrás"""
        self.move_forward(-amount)
    
    def move_left(self, amount):
        """Mueve la cámara hacia la izquierda"""
        lx = math.sin(math.radians(self.yaw - 90))
        lz = -math.cos(math.radians(self.yaw - 90))
        self.x += lx * amount
        self.z += lz * amount
    
    def move_right(self, amount):
        """Mueve la cámara hacia la derecha"""
        self.move_left(-amount)
    
    def move_up(self, amount):
        """Mueve la cámara hacia arriba"""
        self.y += amount
    
    def move_down(self, amount):
        """Mueve la cámara hacia abajo"""
        self.y -= amount
    
    def adjust_zoom(self, delta):
        """Ajusta el zoom (FOV)"""
        self.fov += delta
        self.fov = max(10.0, min(120.0, self.fov))
        # Actualizar coseno del FOV/2
        self._cos_fov_half = math.cos(math.radians(self.fov * 1.65 / 2))
    
    def set_speed_modifier(self, is_slow):
        """Ajusta la velocidad de movimiento"""
        self.speed = self.speed_base * (0.3 if is_slow else 1.0)
        self.sensitivity = self.sensitivity_base * (0.3 if is_slow else 1.0)
