# vector.py
"""
Gestión del vector de apuntado
"""
import math
from pyglet.gl import *
from config import (
    VEC_BASE_X, VEC_BASE_Y, VEC_BASE_Z,
    VEC_YAW, VEC_PITCH, VECTOR_LENGTH,
    COLOR_VECTOR, COLOR_VECTOR_TIP, COLOR_HIT_POINT,
    WORLD_MIN, WORLD_MAX
)


class PointerVector:
    """Clase para gestionar el vector de apuntado"""
    
    def __init__(self, color=COLOR_VECTOR, yaw=VEC_YAW, pitch=VEC_PITCH):
        self.base_x = VEC_BASE_X
        self.base_y = VEC_BASE_Y
        self.base_z = VEC_BASE_Z
        self.yaw = yaw
        self.pitch = pitch
        self.length = VECTOR_LENGTH
        self.color = color
    
    def set_angles(self, yaw, pitch):
        """Setea directamente los ángulos (por ejemplo desde el sensor)"""
        self.yaw = yaw % 360
        self.pitch = max(min(pitch, 89), -89)

    def rotate(self, dyaw, dpitch):
        """Rota el vector"""
        self.yaw += dyaw
        self.pitch += dpitch
        self.pitch = max(min(self.pitch, 89), -89)
        self.yaw %= 360
    
    def get_direction(self):
        """Retorna el vector de dirección normalizado"""
        dx = math.cos(math.radians(self.pitch)) * math.sin(math.radians(self.yaw))
        dy = math.sin(math.radians(self.pitch))
        dz = math.cos(math.radians(self.pitch)) * math.cos(math.radians(self.yaw))
        return dx, dy, dz
    
    def get_end_point(self):
        """Retorna las coordenadas del extremo del vector"""
        dx, dy, dz = self.get_direction()
        return (
            self.base_x + self.length * dx,
            self.base_y + self.length * dy,
            self.base_z + self.length * dz
        )
    
    def calculate_wall_hit(self):
        """
        Calcula el punto de impacto del vector en las paredes/techo
        Returns: (hit_x, hit_y, hit_z) o (None, None, None) si no hay impacto
        """
        dx, dy, dz = self.get_direction()
        hit_x, hit_y, hit_z = None, None, None
        t_hit = float('inf')
        
        # Verificar intersección con cada plano
        planes = [
            ('x', WORLD_MIN, 0), ('x', WORLD_MAX, 0),
            ('y', -1, 1), ('y', WORLD_MAX, 1),
            ('z', WORLD_MIN, 2), ('z', WORLD_MAX, 2)
        ]
        
        for plane, val, axis in planes:
            if axis == 0 and abs(dx) > 0.001:  # Planos X
                t = (val - self.base_x) / dx
                y_test = self.base_y + dy * t
                z_test = self.base_z + dz * t
                if t > 0 and -1 <= y_test <= WORLD_MAX and WORLD_MIN <= z_test <= WORLD_MAX and t < t_hit:
                    hit_x, hit_y, hit_z = val, y_test, z_test
                    t_hit = t
                    
            elif axis == 1 and abs(dy) > 0.001:  # Planos Y
                t = (val - self.base_y) / dy
                x_test = self.base_x + dx * t
                z_test = self.base_z + dz * t
                if t > 0 and WORLD_MIN <= x_test <= WORLD_MAX and WORLD_MIN <= z_test <= WORLD_MAX and t < t_hit:
                    hit_x, hit_y, hit_z = x_test, val, z_test
                    t_hit = t
                    
            elif axis == 2 and abs(dz) > 0.001:  # Planos Z
                t = (val - self.base_z) / dz
                x_test = self.base_x + dx * t
                y_test = self.base_y + dy * t
                if t > 0 and WORLD_MIN <= x_test <= WORLD_MAX and -1 <= y_test <= WORLD_MAX and t < t_hit:
                    hit_x, hit_y, hit_z = x_test, y_test, val
                    t_hit = t
        
        return hit_x, hit_y, hit_z
    
    def draw(self):
        """Dibuja el vector y su punto de impacto"""
        end_x, end_y, end_z = self.get_end_point()
        
        # Dibujar línea del vector
        glColor3f(*self.color)
        glLineWidth(4)
        glBegin(GL_LINES)
        glVertex3f(self.base_x, self.base_y, self.base_z)
        glVertex3f(end_x, end_y, end_z)
        glEnd()
        
        # Dibujar punta del vector
        glColor3f(*COLOR_VECTOR_TIP)
        glPointSize(6)
        glBegin(GL_POINTS)
        glVertex3f(end_x, end_y, end_z)
        glEnd()
        
        # Calcular y dibujar punto de impacto
        hit_x, hit_y, hit_z = self.calculate_wall_hit()
        if hit_x is not None:
            glColor3f(*COLOR_HIT_POINT)
            glPointSize(12)
            glBegin(GL_POINTS)
            glVertex3f(hit_x, hit_y, hit_z)
            glEnd()
        
        return end_x, end_y, end_z, hit_x, hit_y, hit_z
