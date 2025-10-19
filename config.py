# config.py
"""
Configuración global de la aplicación SkyTracker
"""

# Puerto Arduino/ESP32. 
# Configura el puerto antes de utilizarlo.
#
# Linux: /dev/ttyUSB0
# Windows: COM0
#
# Reemplaza el 0 por el valor real.
PORT = "/dev/pts/13"
SIMULATE = True

# Configuración del domo
DOME_RADIUS = 30
DOME_SEGMENTS = 32
DOME_RINGS = 8
USE_DOME = True
DOME_PUSH_FACTOR = 0.99 # Factor para empujar objetos hacia adentro del domo/cúpula

# Configuración de cámara
CAM_YAW = 45.0
CAM_PITCH = -35.26
CAM_X = 3.0
CAM_Y = 3.0
CAM_Z = 3.0
CAM_SPEED_BASE = 0.1
MOUSE_SENSITIVITY_BASE = 0.1

# Configuración del vector
VEC_BASE_X = 0.0
VEC_BASE_Y = 0.0
VEC_BASE_Z = 0.0
VEC_YAW = 45.0
VEC_PITCH = 45.0

# Configuración de visualización
FOV = 80.0
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "SkyTracker - GRUPO 7"

# Ubicación del observador (longitud en grados)
LOCATION_LONGITUDE = -58.229561

# Estrellas de fondo
NUM_BACKGROUND_STARS = 150

# Colores
COLOR_GROUND = (0.0, 0.1, 0.0)
COLOR_GRID = (0.0, 0.3, 0.0)
COLOR_WALLS = (0.0, 0.0, 0.1)
COLOR_STAR = (1.0, 1.0, 0.8)          
COLOR_STAR_BLUE = (0.5, 0.8, 1.0)     
COLOR_STAR_RED = (1.1, 0.5, 0.5)     
COLOR_GALAXY = (0.5, 1.0, 0.5)        
COLOR_PLANET = (1.0, 0.6, 0.2)        
COLOR_MOON = (0.9, 0.9, 1.0)        
COLOR_SUN = (1.0, 1.0, 0.0)           
COLOR_VECTOR = (1.0, 0.0, 0.0)
COLOR_VECTOR_TIP = (1.0, 1.0, 0.0)
COLOR_HIT_POINT = (1.0, 1.0, 1.0)
COLOR_CROSSHAIR = (1.0, 0.0, 0.0)
COLOR_CARDINALS = (0.7, 0.7, 0)

# Tamaños
POINT_SIZE_STAR = 6
POINT_SIZE_BRIGHT_STAR = 8
POINT_SIZE_GALAXY = 8
SPHERE_RADIUS_PLANET = 0.4
SPHERE_RADIUS_MOON = 1.2
SPHERE_RADIUS_SUN = 1.8
CROSSHAIR_SIZE = 10
VECTOR_LENGTH = 3.0

# Umbrales de detección
THRESHOLD_OBJECT = 1.0
THRESHOLD_MOON = 2.0
THRESHOLD_PLANET = 1.5
THRESHOLD_CAMERA = 2.0

# Límites del mundo
WORLD_MIN = -30
WORLD_MAX = 30
WORLD_SCALE = 30
