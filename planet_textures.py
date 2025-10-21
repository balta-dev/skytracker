"""
Sistema de texturas para planetas - CORREGIDO
Carga y aplica texturas realistas a las esferas de planetas
"""
import pyglet
from pyglet.gl import *
import os
import ctypes
from config import SHOW_TEXTURES, POINT_SIZE_GALAXY
from custom_sphere_vbo import draw_sphere
from camera import Camera


class PlanetTextureManager:
    """Gestor de texturas de planetas"""
    
    def __init__(self, textures_folder='textures'):

        self.textures_folder = textures_folder
        self.textures = {}
        self.default_texture = None
        self.current_texture_id = None

        if not SHOW_TEXTURES:
            return
        
        # Mapeo de nombres de planetas a archivos
        self.texture_files = {
            'mercurio': 'mercury.jpg',
            'venus': 'venus.jpg',
            'tierra': 'earth.jpg',
            'marte': 'mars.jpg',
            'jupiter': 'jupiter.jpg',
            'saturno': 'saturn.jpg',
            'urano': 'uranus.jpg',
            'neptuno': 'neptune.jpg',
            'luna': 'moon.jpg',
            'sol': 'sun.jpg',
            # Galaxias (sprites/puntos)
            'andromeda': 'andromeda.png'
        }
        
        self._load_textures()
    
    def _load_textures(self):
        """Carga todas las texturas disponibles"""
        if not os.path.exists(self.textures_folder):
            print(f"WARNING: Carpeta de texturas '{self.textures_folder}' no encontrada")
            print("Creando carpeta y usando colores sólidos...")
            os.makedirs(self.textures_folder, exist_ok=True)
            return
        
        for planet_name, filename in self.texture_files.items():
            filepath = os.path.join(self.textures_folder, filename)
            
            if os.path.exists(filepath):
                try:
                    # Cargar imagen con pyglet
                    image = pyglet.image.load(filepath)
                    
                    # CRÍTICO: Obtener raw ImageData en lugar de la textura manejada
                    # Esto hace que la textura sea independiente del contexto de Pyglet
                    raw_image = image.get_image_data()
                    
                    # Crear textura OpenGL manualmente
                    texture_id = GLuint()
                    glGenTextures(1, ctypes.byref(texture_id))
                    
                    glBindTexture(GL_TEXTURE_2D, texture_id)
                    
                    # Subir datos de la imagen
                    glTexImage2D(
                        GL_TEXTURE_2D, 0, GL_RGBA,
                        raw_image.width, raw_image.height,
                        0, GL_RGBA, GL_UNSIGNED_BYTE,
                        raw_image.get_data('RGBA', raw_image.width * 4)
                    )
                    
                    # Parámetros de textura
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    
                    glBindTexture(GL_TEXTURE_2D, 0)
                    
                    # Guardar ID
                    self.textures[planet_name] = texture_id.value
                    print(f"✓ Textura cargada: {planet_name} ({filename}) - ID: {texture_id.value}")
                    
                except Exception as e:
                    print(f"✗ Error cargando {filename}: {e}")
                    import traceback
                    traceback.print_exc()
    
    def get_texture_id(self, planet_name):
        """
        Obtiene el ID de textura para un planeta
        
        Args:
            planet_name: nombre del planeta (en español o inglés)
        
        Returns:
            texture_id o None si no hay textura
        """
        name_lower = planet_name.lower()
        return self.textures.get(name_lower, None)
    
    def has_texture(self, planet_name):
        """Verifica si existe textura para un planeta"""
        return planet_name.lower() in self.textures


def draw_celestial_objects_with_textures(stars_coords, galaxies_coords, planets_coords, 
                                        moon_coords, planet_sphere_vbo, texture_manager, camera, fov, use_lighting=True):
    """
    Versión con ILUMINACIÓN OPCIONAL para realismo
    
    Args:
        texture_manager: instancia de PlanetTextureManager
        use_lighting: si True, aplica iluminación realista a planetas
    """
    from celestial_data import get_all_celestial_objects
    from config import COLOR_STAR, COLOR_SUN, COLOR_GALAXY, COLOR_PLANET, COLOR_MOON
    from renderer import push_inside_dome
    
    celestial_objects = get_all_celestial_objects()

    # =================================================================
    # CONFIGURAR ILUMINACIÓN SI ESTÁ ACTIVADA
    # =================================================================
    if use_lighting:
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # Luz desde el Sol (posición del Sol si existe)
        sun_pos = None
        for name, x, y, z in stars_coords:
            if name.lower() in ("sun", "sol"):
                sun_pos = (x, y, z)
                break
        
        if sun_pos:
            light_pos = (GLfloat * 4)(sun_pos[0], sun_pos[1], sun_pos[2], 1.0)
        else:
            # Luz por defecto
            light_pos = (GLfloat * 4)(10.0, 10.0, 10.0, 1.0)
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (GLfloat * 4)(0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (GLfloat * 4)(0.5, 0.5, 0.5, 1.0))
        
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
    else:
        glDisable(GL_LIGHTING)

    # =================================================================
    # ESTRELLAS (excluyendo el Sol) - SIN TEXTURAS, SIN ILUMINACIÓN
    # =================================================================
    glDisable(GL_LIGHTING)  # Las estrellas son emisivas
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    for name, x, y, z in stars_coords:
        if name.lower() not in ("sun", "sol"):
            x, y, z = push_inside_dome(x, y, z)
            
            if not camera.is_in_view((x, y, z), fov):
                continue

            obj_data = celestial_objects.get(name.lower(), {"size": 6, "color": list(COLOR_STAR)})
            size = obj_data.get("size", 6)
            color = obj_data.get("color", list(COLOR_STAR))
            
            bright_color = [min(c * 1.25, 1.15) for c in color]
            
            glPointSize(size)
            glColor3f(*bright_color)
            glBegin(GL_POINTS)
            glVertex3f(x, y, z)
            glEnd()
    
    glDisable(GL_POINT_SMOOTH)
    glDisable(GL_BLEND)

    # =================================================================
    # SOL - CON TEXTURA, SIN ILUMINACIÓN (emisivo)
    # =================================================================
    glDisable(GL_LIGHTING)  # El Sol no recibe luz
    
    for name, x, y, z in stars_coords:
        if name.lower() in ("sun", "sol"):
            x, y, z = push_inside_dome(x, y, z)
            
            if not camera.is_in_view((x, y, z), fov):
                continue

            obj_data = celestial_objects.get(name.lower(), {"size": 1.8, "color": list(COLOR_SUN)})
            size = obj_data.get("size", 1.8)
            
            glPushMatrix()
            glTranslatef(x, y, z)
            
            texture_id = texture_manager.get_texture_id(name)
            if texture_id: 
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glColor3f(1.0, 1.0, 1.0)
                draw_sphere(planet_sphere_vbo, size)
                glBindTexture(GL_TEXTURE_2D, 0)
                glDisable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, 0)
                glDisable(GL_TEXTURE_2D)
            else:
                glDisable(GL_TEXTURE_2D)
                color = obj_data.get("color", list(COLOR_SUN))
                glColor3f(*color)
                draw_sphere(planet_sphere_vbo, size)
            
            glPopMatrix()
            break

    # =================================================================
    # GALAXIAS - CON/FALLO DE TEXTURA, SIN ILUMINACIÓN
    # =================================================================
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_POINT_SPRITE)
    glEnable(GL_POINT_SMOOTH)

    # Tamaño base ajustable según FOV
    from config import FOV
    base_size = 100.0
    fov_factor = FOV / fov  # si tu FOV es 60, factor=1, si hacés zoom in FOV=30, factor=2
    point_size = base_size * fov_factor

    # Coeficientes de atenuación por distancia (solo para galaxias)
    attenuation = (0.0, 0.02, 0.001)
    glPointParameterfv(GL_POINT_DISTANCE_ATTENUATION, (GLfloat * 3)(*attenuation))
    glPointParameterf(GL_POINT_FADE_THRESHOLD_SIZE, 1.0)
    glPointParameterf(GL_POINT_SIZE_MIN, 1.0)
    glPointParameterf(GL_POINT_SIZE_MAX, 1024.0)

    texture_id = texture_manager.get_texture_id("andromeda")

    if texture_id is not None:
        # Usamos la textura
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_POINT_SPRITE, GL_COORD_REPLACE, GL_TRUE)
        glPointSize(point_size)
        glColor4f(1, 1, 1, 0.1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_POINTS)
        for name, x, y, z in galaxies_coords:
            if not camera.is_in_view((x, y, z), fov):
                continue
            glVertex3f(x, y, z)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
    else:
        # Si no hay textura:
        glDisable(GL_TEXTURE_2D)
        glPointSize(POINT_SIZE_GALAXY)
        from config import COLOR_GALAXY
        glColor4f(*COLOR_GALAXY, 1) 
        glBegin(GL_POINTS)
        for name, x, y, z in galaxies_coords:
            if not camera.is_in_view((x, y, z), fov):
                continue
            glVertex3f(x, y, z)
        glEnd()

    # Restaurar estado
    glDisable(GL_POINT_SPRITE)
    glDisable(GL_POINT_SMOOTH)
    glDisable(GL_BLEND)
    glColor4f(1.0, 1.0, 1.0, 1.0)


    # =================================================================
    # PLANETAS - CON TEXTURAS Y ILUMINACIÓN
    # =================================================================
    if use_lighting:
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        # Modo que combina textura con iluminación
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    
    for name, x, y, z in planets_coords:
        x, y, z = push_inside_dome(x, y, z)

        if not camera.is_in_view((x, y, z), fov):
            continue

        obj_data = celestial_objects.get(name.lower(), {"size": 0.4, "color": list(COLOR_PLANET)})
        size = obj_data.get("size", 0.4)
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        texture_id = texture_manager.get_texture_id(name)
        if texture_id:
            if use_lighting:
                # Configurar material del planeta
                glMaterialfv(GL_FRONT, GL_DIFFUSE, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
                glMaterialfv(GL_FRONT, GL_AMBIENT, (GLfloat * 4)(0.3, 0.3, 0.3, 1.0))
                glMaterialfv(GL_FRONT, GL_SPECULAR, (GLfloat * 4)(0.1, 0.1, 0.1, 1.0))
                glMaterialf(GL_FRONT, GL_SHININESS, 10.0)
            
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glColor3f(1.0, 1.0, 1.0)
            draw_sphere(planet_sphere_vbo, size)
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, 0)
        else:
            glDisable(GL_TEXTURE_2D)
            color = obj_data.get("color", list(COLOR_PLANET))
            glColor3f(*color)
            draw_sphere(planet_sphere_vbo, size)
            if use_lighting:
                glEnable(GL_TEXTURE_2D)
        
        glPopMatrix()

    # =================================================================
    # LUNA - CON TEXTURA Y ILUMINACIÓN
    # =================================================================
    moon_name = "luna"
    
    moon_coords = push_inside_dome(*moon_coords, 0.9)
    obj_data = celestial_objects.get(moon_name, {"size": 1.2, "color": list(COLOR_MOON)})
    size = obj_data.get("size", 1.2)
    
    if use_lighting:
        glEnable(GL_LIGHTING)
    
    glPushMatrix()
    glTranslatef(*moon_coords)
    
    texture_id = texture_manager.get_texture_id(moon_name)
    if texture_id:
        if use_lighting:
            # Material de la luna (menos brillante)
            glMaterialfv(GL_FRONT, GL_DIFFUSE, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
            glMaterialfv(GL_FRONT, GL_AMBIENT, (GLfloat * 4)(0.2, 0.2, 0.2, 1.0))
            glMaterialfv(GL_FRONT, GL_SPECULAR, (GLfloat * 4)(0.05, 0.05, 0.05, 1.0))
            glMaterialf(GL_FRONT, GL_SHININESS, 5.0)
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)
        draw_sphere(planet_sphere_vbo, size)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
    else:
        glDisable(GL_TEXTURE_2D)
        color = obj_data.get("color", list(COLOR_MOON))
        glColor3f(*color)
        draw_sphere(planet_sphere_vbo, size)
    
    glPopMatrix()
    
    # Restaurar estado
    if use_lighting:
        glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)