"""
Funciones de renderizado de objetos 3D
"""
import math
import pyglet
from pyglet.gl import *
from celestial_data import get_all_celestial_objects  # Importamos para acceder al JSON
from config import (
    WORLD_MIN, WORLD_MAX,
    COLOR_GROUND, COLOR_GRID, COLOR_WALLS,
    COLOR_STAR, COLOR_STAR_BLUE, COLOR_STAR_RED, COLOR_GALAXY, COLOR_PLANET, COLOR_SUN, COLOR_MOON,
    COLOR_VECTOR, COLOR_VECTOR_TIP, COLOR_HIT_POINT,
    COLOR_CROSSHAIR, COLOR_CARDINALS,
    CROSSHAIR_SIZE, USE_DOME, DOME_RADIUS
)


def draw_crosshair(window):
    """Dibuja la cruz de mira en el centro de la pantalla"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window.width, 0, window.height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    
    cx, cy = window.width // 2, window.height // 2
    glColor3f(*COLOR_CROSSHAIR)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(cx - CROSSHAIR_SIZE, cy)
    glVertex2f(cx + CROSSHAIR_SIZE, cy)
    glVertex2f(cx, cy - CROSSHAIR_SIZE)
    glVertex2f(cx, cy + CROSSHAIR_SIZE)
    glEnd()
    
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_environment(background_stars, use_dome=False):
    """Dibuja el entorno (domo o cuadrado)"""
    
    glDisable(GL_BLEND)
    if use_dome:
        from dome_renderer import draw_dome_ground, draw_dome
        draw_dome_ground()
        draw_dome()
    else:
        # Suelo
        glColor3f(*COLOR_GROUND)
        glBegin(GL_QUADS)
        glVertex3f(WORLD_MIN, 0, WORLD_MIN)
        glVertex3f(WORLD_MAX, 0, WORLD_MIN)
        glVertex3f(WORLD_MAX, 0, WORLD_MAX)
        glVertex3f(WORLD_MIN, 0, WORLD_MAX)
        glEnd()
        
        # Rejilla del suelo
        glColor3f(*COLOR_GRID)
        glLineWidth(1)
        glBegin(GL_LINES)
        for i in range(WORLD_MIN, WORLD_MAX + 1, 2):
            glVertex3f(i, 0.01, WORLD_MIN)
            glVertex3f(i, 0.01, WORLD_MAX)
            glVertex3f(WORLD_MIN, 0.01, i)
            glVertex3f(WORLD_MAX, 0.01, i)
        glEnd()
        
        # Paredes
        glColor3f(*COLOR_WALLS)
        for x in [WORLD_MIN, WORLD_MAX]:
            glBegin(GL_QUADS)
            glVertex3f(x, 0, WORLD_MIN)
            glVertex3f(x, WORLD_MAX, WORLD_MIN)
            glVertex3f(x, WORLD_MAX, WORLD_MAX)
            glVertex3f(x, 0, WORLD_MAX)
            glEnd()
        
        for z in [WORLD_MIN, WORLD_MAX]:
            glBegin(GL_QUADS)
            glVertex3f(WORLD_MIN, 0, z)
            glVertex3f(WORLD_MAX, 0, z)
            glVertex3f(WORLD_MAX, WORLD_MAX, z)
            glVertex3f(WORLD_MIN, WORLD_MAX, z)
            glEnd()
        
        # Techo
        glBegin(GL_QUADS)
        glVertex3f(WORLD_MIN, WORLD_MAX, WORLD_MIN)
        glVertex3f(WORLD_MAX, WORLD_MAX, WORLD_MIN)
        glVertex3f(WORLD_MAX, WORLD_MAX, WORLD_MAX)
        glVertex3f(WORLD_MIN, WORLD_MAX, WORLD_MAX)
        glEnd()
    
    # Estrellas de fondo (siempre se dibujan)
    glPointSize(2)
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_POINTS)
    for s in background_stars:
        glVertex3f(*s)
    glEnd()


def push_inside_dome(x, y, z, factor=None):
    """Empuja un punto ligeramente hacia adentro del domo para evitar clipping."""
    from config import DOME_PUSH_FACTOR
    if factor is None:
        factor = DOME_PUSH_FACTOR
    length = math.sqrt(x*x + y*y + z*z)
    if length > 0:
        scale = (length * factor) / length
        return x * scale, y * scale, z * scale
    return x, y, z


def draw_celestial_objects(stars_coords, galaxies_coords, planets_coords, moon_coords, sphere_quad):
    """Dibuja todos los objetos celestes usando tamaños y colores del JSON"""

    # FORZAR depth test en modo lectura+escritura
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glDepthMask(GL_TRUE)  # Las estrellas SÍ escriben en depth buffer

    # Obtener datos del JSON para referencia de tamaños y colores
    celestial_objects = get_all_celestial_objects()

    # Estrellas (excluyendo el Sol) - con efecto de brillo
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    for name, x, y, z in stars_coords:
        if name.lower() != "sun" and name.lower() != "sol":  # Excluimos el Sol
            x, y, z = push_inside_dome(x, y, z)
            # Obtener datos del diccionario (o usar valores por defecto si no existe)
            obj_data = celestial_objects.get(name.lower(), {"size": 6, "color": COLOR_STAR})
            size = obj_data.get("size", 6)
            color = obj_data.get("color", [c for c in COLOR_STAR])
            
            # Dibujar la estrella con brillo intensificado
            glPointSize(size)
            # Aumentar el brillo del color (valores > 1.0 para efecto HDR simulado)
            bright_color = [min(c * 1.25, 1.1) for c in color]
            glColor3f(*bright_color)
            glBegin(GL_POINTS)
            glVertex3f(x, y, z)
            glEnd()
    
    glDisable(GL_POINT_SMOOTH)
    glDisable(GL_BLEND)

    # Renderizar el Sol como esfera
    for name, x, y, z in stars_coords:
        if name.lower() == "sun" or name.lower() == "sol":
            x, y, z = push_inside_dome(x, y, z)
            obj_data = celestial_objects.get(name.lower(), {"size": 1.8, "color": COLOR_SUN})
            size = obj_data.get("size", 1.8)
            color = obj_data.get("color", [c for c in COLOR_SUN])  # Convertir tupla a lista si es necesario
            glPushMatrix()
            glTranslatef(x, y, z)
            glColor3f(*color)
            gluSphere(sphere_quad, size, 20, 20)
            glPopMatrix()

    # Galaxias
    for name, x, y, z in galaxies_coords:
        obj_data = celestial_objects.get(name.lower(), {"size": 8, "color": COLOR_GALAXY})
        size = obj_data.get("size", 8)
        color = obj_data.get("color", [c for c in COLOR_GALAXY])  # Convertir tupla a lista si es necesario
        glPointSize(size)
        glColor3f(*color)
        glBegin(GL_POINTS)
        glVertex3f(x, y, z)
        glEnd()

    # Planetas
    for name, x, y, z in planets_coords:
        obj_data = celestial_objects.get(name.lower(), {"size": 0.4, "color": COLOR_PLANET})
        size = obj_data.get("size", 0.4)
        color = obj_data.get("color", [c for c in COLOR_PLANET])  # Convertir tupla a lista si es necesario
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(*color)
        gluSphere(sphere_quad, size, 12, 12)
        glPopMatrix()

    # Luna
    moon_name = "luna"
    obj_data = celestial_objects.get(moon_name, {"size": 1.2, "color": COLOR_MOON})
    size = obj_data.get("size", 1.2)
    color = obj_data.get("color", [c for c in COLOR_MOON])  # Convertir tupla a lista si es necesario
    glPushMatrix()
    glTranslatef(*moon_coords)
    glColor3f(*color)
    gluSphere(sphere_quad, size, 16, 16)
    glPopMatrix()


def draw_cardinals():
    """Dibuja los puntos cardinales en las paredes"""
    def draw_3d_letter(letter, x, y, z, size=0.5):
        glPushMatrix()
        glTranslatef(x, y, z)
        angle_to_center = math.degrees(math.atan2(x, z))
        glRotatef(-angle_to_center + 180, 0, 1, 0)
        glLineWidth(3)
        glBegin(GL_LINES)
        if letter == 'N':
            glVertex3f(-size/2, -size, 0)
            glVertex3f(-size/2, size, 0)
            glVertex3f(-size/2, size, 0)
            glVertex3f(size/2, -size, 0)
            glVertex3f(size/2, -size, 0)
            glVertex3f(size/2, size, 0)
        elif letter == 'S':
            glVertex3f(size/2, size, 0)
            glVertex3f(-size/2, size, 0)
            glVertex3f(-size/2, size, 0)
            glVertex3f(-size/2, 0, 0)
            glVertex3f(-size/2, 0, 0)
            glVertex3f(size/2, 0, 0)
            glVertex3f(size/2, 0, 0)
            glVertex3f(size/2, -size, 0)
            glVertex3f(size/2, -size, 0)
            glVertex3f(-size/2, -size, 0)
        elif letter == 'E':
            glVertex3f(size/2, -size, 0)
            glVertex3f(size/2, size, 0)
            glVertex3f(size/2, size, 0)
            glVertex3f(-size/2, size, 0)
            glVertex3f(size/2, 0, 0)
            glVertex3f(-size/2, 0, 0)
            glVertex3f(size/2, -size, 0)
            glVertex3f(-size/2, -size, 0)
        elif letter == 'O':
            segments = 8
            for i in range(segments):
                angle1 = (i / segments) * 2 * math.pi
                angle2 = ((i + 1) / segments) * 2 * math.pi
                glVertex3f(math.cos(angle1) * size/2, math.sin(angle1) * size, 0)
                glVertex3f(math.cos(angle2) * size/2, math.sin(angle2) * size, 0)
        glEnd()
        glPopMatrix()

    glColor3f(*COLOR_CARDINALS)
    
    if USE_DOME:
        # Posicionar en el horizonte del domo (phi = 90°, diferentes azimuts)
        y_horizon = -1  # En el horizonte
        
        # Norte (z negativo)
        draw_3d_letter('N', 0, y_horizon + 2, -DOME_RADIUS * 0.95, 0.8)
        # Sur (z positivo)
        draw_3d_letter('S', 0, y_horizon + 2, DOME_RADIUS * 0.95, 0.8)
        # Este (x positivo)
        draw_3d_letter('E', DOME_RADIUS * 0.95, y_horizon + 2, 0, 0.8)
        # Oeste (x negativo)
        draw_3d_letter('O', -DOME_RADIUS * 0.95, y_horizon + 2, 0, 0.8)
    else:
        # Posiciones para el cubo
        draw_3d_letter('N', 0, 2, -19.5, 0.6)
        draw_3d_letter('S', 0, 2, 19.5, 0.6)
        draw_3d_letter('E', 19.5, 2, 0, 0.6)
        draw_3d_letter('O', -19.5, 2, 0, 0.6)


def draw_text_2d(window, lines, start_y):
    """Dibuja texto 2D en pantalla"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window.width, 0, window.height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    
    y = start_y
    for line in lines:
        pyglet.text.Label(
            line, 
            x=10, 
            y=y, 
            color=(255, 255, 255, 255), 
            font_size=12
        ).draw()
        y -= 20
    
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


class CachedTextRenderer:
    """Renderizador de texto 2D optimizado con caché y batch."""

    def __init__(self):
        self.labels = []
        self.batch = pyglet.graphics.Batch()
        self.num_lines = 0

    def draw(self, window, lines, start_y):
        """Dibuja texto 2D en pantalla con mejor performance."""

        # Ajustar cantidad de labels si cambió el número de líneas
        while len(self.labels) < len(lines):
            self.labels.append(
                pyglet.text.Label(
                    "",
                    x=10,
                    y=0,
                    color=(255, 255, 255, 255),
                    font_size=12,
                    batch=self.batch
                )
            )
        while len(self.labels) > len(lines):
            lbl = self.labels.pop()
            lbl.delete()

        # Actualizar texto y posición sin recrear labels
        y = start_y
        for i, line in enumerate(lines):
            self.labels[i].text = line
            self.labels[i].y = y
            y -= 20

        self.num_lines = len(lines)

        # Configurar proyección ortográfica solo una vez
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, window.width, 0, window.height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # Dibujar todas las líneas de texto en una sola draw call
        if self.num_lines > 0:
            self.batch.draw()

        # Restaurar estado
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)