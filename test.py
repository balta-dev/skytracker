"""
Renderizador de esferas usando gluSphere
"""
import os
import pyglet
from pyglet.gl import *

# -----------------------------
# Funciones de dibujo con gluSphere
# -----------------------------
def draw_textured_sphere(x, y, z, radius, texture_id, detail=32):
    glPushMatrix()
    glTranslatef(x, y, z)
    
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor3f(1.0, 1.0, 1.0)
    
    # Crear quadric y configurar texturas
    quad = gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE)
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluQuadricDrawStyle(quad, GLU_FILL)
    
    # Dibujar esfera
    gluSphere(quad, radius, detail, detail)
    gluDeleteQuadric(quad)
    
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_colored_sphere(x, y, z, radius, color, detail=16):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    
    # Crear quadric
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluQuadricDrawStyle(quad, GLU_FILL)
    
    # Dibujar esfera
    gluSphere(quad, radius, detail, detail)
    gluDeleteQuadric(quad)
    
    glPopMatrix()

# -----------------------------
# Ventana Pyglet
# -----------------------------
window = pyglet.window.Window(800, 600, "Test Esfera con gluSphere")

# Intentar cargar textura
texture_id = None
if os.path.exists('textures/mars.jpg'):
    try:
        image = pyglet.image.load('textures/mars.jpg')
        texture_id = image.get_texture().id
        print(f"✓ Textura cargada: ID {texture_id}")
    except Exception as e:
        print(f"✗ Error cargando textura: {e}")
else:
    print("⚠ No se encuentra textures/mars.jpg")

rotation = 0.0  # rotación global

# -----------------------------
# Luz básica para realismo
# -----------------------------
def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(5.0, 5.0, 10.0, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)

setup_lighting()

# -----------------------------
# Función de actualización
# -----------------------------
def update(dt):
    global rotation
    rotation += 30 * dt  # grados por segundo

pyglet.clock.schedule(update)

# -----------------------------
# Eventos de Pyglet
# -----------------------------
@window.event
def on_draw():
    global rotation
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Configurar proyección
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, window.width / window.height, 0.1, 100.0)
    
    # Configurar vista
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0, 0, -5)
    glRotatef(rotation, 0, 1, 0)
    
    glEnable(GL_DEPTH_TEST)
    
    # Esfera izquierda (textura si existe)
    if texture_id:
        draw_textured_sphere(-1.5, 0, 0, 0.8, texture_id, detail=32)
    else:
        draw_colored_sphere(-1.5, 0, 0, 0.8, (1.0, 0.5, 0.2))
    
    # Esfera derecha (color sólido verde)
    draw_colored_sphere(1.5, 0, 0, 0.8, (0.2, 1.0, 0.2))

@window.event
def on_resize(width, height):
    glViewport(0, 0, width, height)

# -----------------------------
# Ejecutar aplicación
# -----------------------------
pyglet.app.run()