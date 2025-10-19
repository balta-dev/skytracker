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
    WORLD_MIN, WORLD_MAX, USE_DOME, DOME_RADIUS
)
from renderer import push_inside_dome


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

    def calculate_dome_hit(self):
        """
        Calcula el punto de impacto del vector en el domo hemisférico
        Returns: (hit_x, hit_y, hit_z) o (None, None, None) si no hay impacto
        """
        dx, dy, dz = self.get_direction()
        
        # Resolver: |P + t*D|² = R²
        # Donde P = (base_x, base_y, base_z), D = (dx, dy, dz)
        py = self.base_y
        
        a = dx*dx + dy*dy + dz*dz
        b = 2*(self.base_x*dx + py*dy + self.base_z*dz)
        c = self.base_x**2 + py**2 + self.base_z**2 - DOME_RADIUS**2
        
        discriminant = b*b - 4*a*c
        if discriminant < 0:
            return None, None, None
        
        t1 = (-b + math.sqrt(discriminant)) / (2*a)
        t2 = (-b - math.sqrt(discriminant)) / (2*a)
        
        # Tomar la intersección positiva más cercana
        t = None
        if t1 > 0 and t2 > 0:
            t = min(t1, t2)
        elif t1 > 0:
            t = t1
        elif t2 > 0:
            t = t2
        
        if t is None or t <= 0:
            return None, None, None
        
        hit_x = self.base_x + t * dx
        hit_y = self.base_y + t * dy
        hit_z = self.base_z + t * dz
        
        # Solo aceptar si está en el hemisferio superior (y >= 0)
        if hit_y < 0:
            return None, None, None
        
        hit_x, hit_y, hit_z = push_inside_dome(hit_x, hit_y, hit_z)
        return hit_x, hit_y, hit_z
    
    def draw(self, color=COLOR_VECTOR, crosshair=COLOR_HIT_POINT):
        end_x, end_y, end_z = self.get_end_point()
        
        # Línea vector (IGUAL)
        glColor3f(*color)
        glLineWidth(4)
        glBegin(GL_LINES)
        glVertex3f(self.base_x, self.base_y, self.base_z)
        glVertex3f(end_x, end_y, end_z)
        glEnd()
        
        # Punta (IGUAL)
        glColor3f(*COLOR_VECTOR_TIP)
        glPointSize(6)
        glBegin(GL_POINTS)
        glVertex3f(end_x, end_y, end_z)
        glEnd()
        
        # Impacto
        if USE_DOME:
            hit_x, hit_y, hit_z = self.calculate_dome_hit()
        else:
            hit_x, hit_y, hit_z = self.calculate_wall_hit()
        
        if hit_x is not None:
            self._draw_circle_perpendicular(hit_x, hit_y, hit_z, end_x, end_y, end_z, crosshair)
        
        return end_x, end_y, end_z, hit_x, hit_y, hit_z


    def _draw_circle_perpendicular(self, x, y, z, from_x, from_y, from_z, crosshair):
        """CÍRCULO PERPENDICULAR AL VECTOR"""
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Vector dirección
        dx, dy, dz = x - from_x, y - from_y, z - from_z
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length > 0:
            dx, dy, dz = dx/length, dy/length, dz/length
        
        # Rotar círculo para que esté PERPENDICULAR
        yaw = math.degrees(math.atan2(dx, dz))
        pitch = math.degrees(math.asin(dy))
        
        glRotatef(yaw, 0, 1, 0)
        glRotatef(-pitch, 1, 0, 0)
        
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        
        # CÍRCULO HUECO
        glColor4f(*crosshair, 0.6)
        glLineWidth(2.0)
        segments = 16
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            glVertex3f(math.cos(angle) * 0.4, math.sin(angle) * 0.4, 0)
        glEnd()
        
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
