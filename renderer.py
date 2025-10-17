# renderer.py
"""
Funciones de renderizado de objetos 3D
"""
import math
import pyglet
from pyglet.gl import *
from config import (
    WORLD_MIN, WORLD_MAX,
    COLOR_GROUND, COLOR_GRID, COLOR_WALLS,
    COLOR_STAR, COLOR_GALAXY, COLOR_PLANET, COLOR_MOON,
    COLOR_CROSSHAIR, COLOR_CARDINALS,
    POINT_SIZE_STAR, POINT_SIZE_GALAXY,
    SPHERE_RADIUS_PLANET, SPHERE_RADIUS_MOON,
    CROSSHAIR_SIZE
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
    
    if use_dome:
        from dome_renderer import draw_dome_ground, draw_dome
        draw_dome_ground()
        draw_dome()
    else:
        # Suelo
        glColor3f(*COLOR_GROUND)
        glBegin(GL_QUADS)
        glVertex3f(WORLD_MIN, -1, WORLD_MIN)
        glVertex3f(WORLD_MAX, -1, WORLD_MIN)
        glVertex3f(WORLD_MAX, -1, WORLD_MAX)
        glVertex3f(WORLD_MIN, -1, WORLD_MAX)
        glEnd()
        
        # Rejilla del suelo
        glColor3f(*COLOR_GRID)
        glLineWidth(1)
        glBegin(GL_LINES)
        for i in range(WORLD_MIN, WORLD_MAX + 1, 2):
            glVertex3f(i, -0.99, WORLD_MIN)
            glVertex3f(i, -0.99, WORLD_MAX)
            glVertex3f(WORLD_MIN, -0.99, i)
            glVertex3f(WORLD_MAX, -0.99, i)
        glEnd()
        
        # Paredes
        glColor3f(*COLOR_WALLS)
        for x in [WORLD_MIN, WORLD_MAX]:
            glBegin(GL_QUADS)
            glVertex3f(x, -1, WORLD_MIN)
            glVertex3f(x, WORLD_MAX, WORLD_MIN)
            glVertex3f(x, WORLD_MAX, WORLD_MAX)
            glVertex3f(x, -1, WORLD_MAX)
            glEnd()
        
        for z in [WORLD_MIN, WORLD_MAX]:
            glBegin(GL_QUADS)
            glVertex3f(WORLD_MIN, -1, z)
            glVertex3f(WORLD_MAX, -1, z)
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
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_POINTS)
    for s in background_stars:
        glVertex3f(*s)
    glEnd()


def draw_celestial_objects(stars_coords, galaxies_coords, planets_coords, moon_coords, sphere_quad):
    """Dibuja todos los objetos celestes"""
    # Estrellas
    glPointSize(POINT_SIZE_STAR)
    glColor3f(*COLOR_STAR)
    glBegin(GL_POINTS)
    for _, x, y, z in stars_coords:
        glVertex3f(x, y, z)
    glEnd()
    
    # Galaxias
    glPointSize(POINT_SIZE_GALAXY)
    glColor3f(*COLOR_GALAXY)
    glBegin(GL_POINTS)
    for _, x, y, z in galaxies_coords:
        glVertex3f(x, y, z)
    glEnd()
    
    # Planetas
    glColor3f(*COLOR_PLANET)
    for _, x, y, z in planets_coords:
        glPushMatrix()
        glTranslatef(x, y, z)
        gluSphere(sphere_quad, SPHERE_RADIUS_PLANET, 12, 12)
        glPopMatrix()
    
    # Luna
    glColor3f(*COLOR_MOON)
    glPushMatrix()
    glTranslatef(*moon_coords)
    gluSphere(sphere_quad, SPHERE_RADIUS_MOON, 16, 16)
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