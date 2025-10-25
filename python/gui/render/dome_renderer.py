# dome_renderer.py
"""
Renderizado de domo hemisférico
"""
import math
from pyglet.gl import *
from config import COLOR_WALLS, DOME_RADIUS, DOME_SEGMENTS, DOME_RINGS, ENABLE_DRAW_DOME
from gui.controls.camera import Camera


def draw_dome(enabled = ENABLE_DRAW_DOME):
    """Dibuja un domo hemisférico"""
    
    if not enabled:
        return

    glColor3f(*COLOR_WALLS)
    
    for ring in range(DOME_RINGS):
        glBegin(GL_QUAD_STRIP)
        for seg in range(DOME_SEGMENTS + 1):
            # Ángulos
            theta = (seg / DOME_SEGMENTS) * 2 * math.pi
            phi1 = (ring / DOME_RINGS) * (math.pi / 2)
            phi2 = ((ring + 1) / DOME_RINGS) * (math.pi / 2)
            
            # Primera fila de vértices
            x1 = DOME_RADIUS * math.sin(phi1) * math.cos(theta)
            z1 = DOME_RADIUS * math.sin(phi1) * math.sin(theta)
            y1 = DOME_RADIUS * math.cos(phi1)
            
            # Segunda fila de vértices
            x2 = DOME_RADIUS * math.sin(phi2) * math.cos(theta)
            z2 = DOME_RADIUS * math.sin(phi2) * math.sin(theta)
            y2 = DOME_RADIUS * math.cos(phi2)
            
            glVertex3f(x1, y1, z1)
            glVertex3f(x2, y2, z2)
        glEnd()


def draw_dome_ground():
    """Dibuja el suelo circular del domo"""
    from config import COLOR_GROUND, COLOR_GRID
    
    # Suelo
    glColor3f(*COLOR_GROUND)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)  # Centro
    for i in range(DOME_SEGMENTS + 1):
        angle = (i / DOME_SEGMENTS) * 2 * math.pi
        x = DOME_RADIUS * math.cos(angle)
        z = DOME_RADIUS * math.sin(angle)
        glVertex3f(x, 0, z)
    glEnd()
    
    # Rejilla circular
    glColor3f(*COLOR_GRID)
    glLineWidth(1)
    
    # Líneas radiales
    glBegin(GL_LINES)
    for i in range(DOME_SEGMENTS):
        angle = (i / DOME_SEGMENTS) * 2 * math.pi
        x = DOME_RADIUS * math.cos(angle)
        z = DOME_RADIUS * math.sin(angle)
        glVertex3f(0, 0.01, 0)
        glVertex3f(x, 0.01, z)
    glEnd()
    
    # Círculos concéntricos
    num_circles = 10
    for circle in range(1, num_circles + 1):
        radius = (circle / num_circles) * DOME_RADIUS
        glBegin(GL_LINE_LOOP)
        for i in range(DOME_SEGMENTS):
            angle = (i / DOME_SEGMENTS) * 2 * math.pi
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            glVertex3f(x, 0.01, z)
        glEnd()

_dome_list = None
_ground_list = None

def draw_dome_optimized():
    global _dome_list, _ground_list
    if _dome_list is None:
        _dome_list = glGenLists(1)
        glNewList(_dome_list, GL_COMPILE)
        draw_dome()
        glEndList()
    if _ground_list is None:
        _ground_list = glGenLists(1)
        glNewList(_ground_list, GL_COMPILE)
        draw_dome_ground()
        glEndList()

    glCallList(_ground_list)
    glCallList(_dome_list)