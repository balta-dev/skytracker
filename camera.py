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
        dz = math.cos(math.radians(self.pitch)) * math.cos(math.radians(self.yaw))
        return dx, dy, dz
    
    def rotate(self, dx, dy):
        """Rota la cámara según el movimiento del mouse"""
        self.yaw -= dx * self.sensitivity
        self.pitch += dy * self.sensitivity
        self.pitch = max(min(self.pitch, 89), -89)
        self.yaw %= 360
    
    def move_forward(self, amount):
        """Mueve la cámara hacia adelante"""
        fx = math.sin(math.radians(self.yaw))
        fz = math.cos(math.radians(self.yaw))
        self.x += fx * amount
        self.z += fz * amount
    
    def move_backward(self, amount):
        """Mueve la cámara hacia atrás"""
        self.move_forward(-amount)
    
    def move_left(self, amount):
        """Mueve la cámara hacia la izquierda"""
        lx = math.sin(math.radians(self.yaw - 90))
        lz = math.cos(math.radians(self.yaw - 90))
        self.x -= lx * amount
        self.z -= lz * amount
    
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
    
    def set_speed_modifier(self, is_slow):
        """Ajusta la velocidad de movimiento"""
        self.speed = self.speed_base * (0.3 if is_slow else 1.0)
        self.sensitivity = self.sensitivity_base * (0.3 if is_slow else 1.0)
