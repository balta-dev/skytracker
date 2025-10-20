"""
Funciones de renderizado de objetos 3D - OPTIMIZADO
"""
import math
import pyglet
from pyglet.gl import *
from celestial_data import get_all_celestial_objects
from config import (
    WORLD_MIN, WORLD_MAX,
    COLOR_GROUND, COLOR_GRID, COLOR_WALLS,
    COLOR_STAR, COLOR_STAR_BLUE, COLOR_STAR_RED, COLOR_GALAXY, COLOR_PLANET, COLOR_SUN, COLOR_MOON,
    COLOR_VECTOR, COLOR_VECTOR_TIP, COLOR_HIT_POINT,
    COLOR_CROSSHAIR, COLOR_CARDINALS,
    CROSSHAIR_SIZE, USE_DOME, DOME_RADIUS
)


# ============================================================
# CACHE GLOBAL PARA DATOS CELESTIALES
# ============================================================
_celestial_cache = None

def get_cached_celestial_data():
    """Cache de datos celestiales para evitar búsquedas repetitivas"""
    global _celestial_cache
    if _celestial_cache is None:
        _celestial_cache = get_all_celestial_objects()
    return _celestial_cache


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
        from dome_renderer import draw_dome_ground, draw_dome_optimized
        draw_dome_ground()
        draw_dome_optimized()
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
    glColor3f(0.3, 0.3, 0.3)
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


# ============================================================
# OPTIMIZACIÓN: Batch rendering con VBOs
# ============================================================
class CelestialRenderer:
    """Renderizador optimizado de objetos celestiales usando batching"""
    
    def __init__(self, sphere_quad):
        self.sphere_quad = sphere_quad
        self.celestial_data = get_cached_celestial_data()
        
        # Pre-cache de colores y tamaños para evitar lookups
        self.star_cache = {}
        self.galaxy_cache = {}
        self.planet_cache = {}
        
    def _get_object_data(self, name, cache, default_size, default_color):
        """Obtiene datos del objeto con cache"""
        if name not in cache:
            obj_data = self.celestial_data.get(name.lower(), {
                "size": default_size, 
                "color": list(default_color)
            })
            cache[name] = (obj_data["size"], obj_data["color"])
        return cache[name]
    
    def draw_stars_batch(self, stars_coords):
        """Dibuja todas las estrellas en un solo batch (excepto el Sol)"""
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)
        
        # Agrupar estrellas por tamaño para minimizar cambios de estado
        stars_by_size = {}
        
        for name, x, y, z in stars_coords:
            if name.lower() in ("sun", "sol"):
                continue
                
            size, color = self._get_object_data(name, self.star_cache, 6, COLOR_STAR)
            
            if size not in stars_by_size:
                stars_by_size[size] = []
            
            x, y, z = push_inside_dome(x, y, z)
            bright_color = [min(c * 1.25, 1.1) for c in color]
            stars_by_size[size].append((x, y, z, bright_color))
        
        # Dibujar agrupadas por tamaño
        for size, stars in stars_by_size.items():
            glPointSize(size)
            glBegin(GL_POINTS)
            for x, y, z, color in stars:
                glColor3f(*color)
                glVertex3f(x, y, z)
            glEnd()
        
        glDisable(GL_POINT_SMOOTH)
        glDisable(GL_BLEND)
    
    def draw_sun(self, stars_coords):
        """Dibuja el Sol como esfera"""
        for name, x, y, z in stars_coords:
            if name.lower() in ("sun", "sol"):
                x, y, z = push_inside_dome(x, y, z)
                size, color = self._get_object_data(name, self.star_cache, 1.8, COLOR_SUN)
                
                glPushMatrix()
                glTranslatef(x, y, z)
                glColor3f(*color)
                gluSphere(self.sphere_quad, size, 20, 20)
                glPopMatrix()
                break
    
    def draw_galaxies_batch(self, galaxies_coords):
        """Dibuja todas las galaxias en un solo batch"""
        # Agrupar por tamaño
        galaxies_by_size = {}
        
        for name, x, y, z in galaxies_coords:
            size, color = self._get_object_data(name, self.galaxy_cache, 8, COLOR_GALAXY)
            
            if size not in galaxies_by_size:
                galaxies_by_size[size] = []
            
            galaxies_by_size[size].append((x, y, z, color))
        
        # Dibujar agrupadas
        for size, galaxies in galaxies_by_size.items():
            glPointSize(size)
            glBegin(GL_POINTS)
            for x, y, z, color in galaxies:
                glColor3f(*color)
                x, y, z = push_inside_dome(x, y, z)
                glVertex3f(x, y, z)
            glEnd()
    
    def draw_planets_batch(self, planets_coords):
        """Dibuja todos los planetas"""
        for name, x, y, z in planets_coords:
            size, color = self._get_object_data(name, self.planet_cache, 0.4, COLOR_PLANET)
            x, y, z = push_inside_dome(x, y, z)
            glPushMatrix()
            glTranslatef(x, y, z)
            glColor3f(*color)
            gluSphere(self.sphere_quad, size, 12, 12)
            glPopMatrix()
    
    def draw_moon(self, moon_coords):
        """Dibuja la Luna"""
        size, color = self._get_object_data("luna", self.planet_cache, 1.2, COLOR_MOON)
        
        glPushMatrix()
        glTranslatef(*moon_coords)
        glColor3f(*color)
        gluSphere(self.sphere_quad, size, 16, 16)
        glPopMatrix()


def draw_celestial_objects(stars_coords, galaxies_coords, planets_coords, moon_coords, sphere_quad):
    """Dibuja todos los objetos celestes - VERSIÓN OPTIMIZADA"""
    
    # Usar renderer singleton (se crea una sola vez)
    if not hasattr(draw_celestial_objects, '_renderer'):
        draw_celestial_objects._renderer = CelestialRenderer(sphere_quad)
    
    renderer = draw_celestial_objects._renderer
    
    # Configurar estado OpenGL una sola vez
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glDepthMask(GL_TRUE)
    
    # Dibujar en orden óptimo (menos cambios de estado)
    renderer.draw_stars_batch(stars_coords)
    renderer.draw_sun(stars_coords)
    renderer.draw_galaxies_batch(galaxies_coords)
    renderer.draw_planets_batch(planets_coords)
    renderer.draw_moon(moon_coords)


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
        y_horizon = -1
        draw_3d_letter('N', 0, y_horizon + 2, -DOME_RADIUS * 0.95, 0.8)
        draw_3d_letter('S', 0, y_horizon + 2, DOME_RADIUS * 0.95, 0.8)
        draw_3d_letter('E', DOME_RADIUS * 0.95, y_horizon + 2, 0, 0.8)
        draw_3d_letter('O', -DOME_RADIUS * 0.95, y_horizon + 2, 0, 0.8)
    else:
        draw_3d_letter('N', 0, 2, -19.5, 0.6)
        draw_3d_letter('S', 0, 2, 19.5, 0.6)
        draw_3d_letter('E', 19.5, 2, 0, 0.6)
        draw_3d_letter('O', -19.5, 2, 0, 0.6)


def draw_text_2d(window, lines, start_y):
    """Dibuja texto 2D en pantalla (legacy - usar CachedTextRenderer)"""
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
        self.last_width = 0
        self.last_height = 0

    def draw(self, window, lines, start_y):
        """Dibuja texto 2D en pantalla con mejor performance."""
        
        # Detectar si cambió el tamaño de ventana (necesita recrear proyección)
        window_resized = (self.last_width != window.width or 
                         self.last_height != window.height)
        if window_resized:
            self.last_width = window.width
            self.last_height = window.height

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

        # Actualizar texto y posición solo si cambió
        y = start_y
        for i, line in enumerate(lines):
            if self.labels[i].text != line:
                self.labels[i].text = line
            if self.labels[i].y != y:
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