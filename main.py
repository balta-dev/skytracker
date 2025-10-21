"""
SkyTracker - Aplicación principal OPTIMIZADA con TEXTURAS
Programa de visualización astronómica 3D
"""
import pyglet
from pyglet.gl import *
from pyglet.window import key
from datetime import datetime, timezone
import random

# Importar módulos del proyecto
from config import *
from celestial_data import REAL_STARS, GALAXIES, PLANETS, MOON_RA_DEC
from astronomy import calculate_lst, ra_dec_to_xyz
from camera import Camera
from vector import PointerVector
from renderer import (
    draw_crosshair, draw_environment, 
    draw_cardinals, draw_text_2d, CachedTextRenderer
)
from ui import SearchBox, InfoDisplay
from object_detection import (
    detect_pointed_object_by_vector,
    detect_looked_object_by_camera
)
from tracker import ObjectTracker
from input_handler import InputHandler
from serial_comm import SerialComm
from bloom_renderer import BloomRenderer
from profiling_tools import profiler

# ============================================================
# IMPORTAR SISTEMA DE TEXTURAS
# ============================================================
from planet_textures import PlanetTextureManager, draw_celestial_objects_with_textures
from custom_sphere_vbo import create_sphere_vertex_list

import time


class CoordinateCache:
    """Cache de coordenadas celestiales para evitar recalcular proyecciones"""
    
    def __init__(self):
        self.last_lst_h = None
        self.stars_coords = []
        self.galaxies_coords = []
        self.planets_coords = []
        self.moon_coords = None
        self.projection_func = None
        self.projection_kwargs = {}
        
        # Umbral de cambio para actualizar (en horas)
        self.update_threshold = 0.001  # ~3.6 segundos
    
    def should_update(self, lst_h):
        """Determina si necesita actualizar las coordenadas"""
        if self.last_lst_h is None:
            return True
        
        # Calcular diferencia considerando el wrap en 24h
        diff = abs(lst_h - self.last_lst_h)
        if diff > 12:  # Si la diferencia es mayor a 12h, tomamos el camino corto
            diff = 24 - diff
        
        return diff >= self.update_threshold
    
    def update(self, lst_h, projection_func, projection_kwargs):
        """Actualiza todas las coordenadas celestiales"""
        self.last_lst_h = lst_h
        self.projection_func = projection_func
        self.projection_kwargs = projection_kwargs
        
        # Proyectar todos los objetos
        self.stars_coords = [
            (name, *projection_func(ra, dec, lst_h, **projection_kwargs))
            for name, ra, dec, size in REAL_STARS
        ]
        
        self.galaxies_coords = [
            (name, *projection_func(ra, dec, lst_h, **projection_kwargs))
            for name, ra, dec, size in GALAXIES
        ]
        
        self.planets_coords = [
            (name, *projection_func(ra, dec, lst_h, **projection_kwargs))
            for name, ra, dec, size in PLANETS
        ]
        
        self.moon_coords = projection_func(
            MOON_RA_DEC[0], MOON_RA_DEC[1], lst_h, **projection_kwargs
        )


class SkyTrackerApp:
    """Clase principal de la aplicación SkyTracker"""
    
    def __init__(self):
        
        display = pyglet.canvas.get_display()
        screen = display.get_default_screen()

        # Crear ventana
        self.window = pyglet.window.Window(
            screen.width, screen.height, 
            WINDOW_TITLE, 
            resizable=True,
            vsync=False
        )
        self.window.set_minimum_size(400, 300)
        self.window.set_exclusive_mouse(True)
        self.window.on_close = self.on_close

        # ============================================================
        # INICIALIZAR GESTOR DE TEXTURAS
        # ============================================================
        print("\n=== Inicializando sistema de texturas ===")
        self.texture_manager = PlanetTextureManager(textures_folder='textures')
        print(f"Texturas cargadas: {len(self.texture_manager.textures)}")
        print("=" * 45 + "\n")

        # Para usar la placa real:
        if not SIMULATE:
            self.serial_device = SerialComm(port=PORT, baudrate=115200, simulate=False)
        else:
            self.serial_device = SerialComm(simulate=True)

        # Buffer de simulación de retardo
        self.simulated_delay_buffer = []
        self.simulated_delay_seconds = 0.6

        # FPS display
        self.fps_display = pyglet.window.FPSDisplay(window=self.window)

        # Renderer de texto cacheado
        self.text_renderer = CachedTextRenderer()
        
        # Renderizar Bloom
        self.bloom = BloomRenderer(self.window.width, self.window.height)

        # Cache de coordenadas celestiales
        self.coord_cache = CoordinateCache()

        # Componentes
        self.camera = Camera()
        self.vector = PointerVector(color=COLOR_VECTOR)
        self.sensor_vector = PointerVector(color=(0.0, 1.0, 0.0), yaw=90.0, pitch=90.0)
        self.search_box = SearchBox()
        self.tracker = ObjectTracker()
        self.input_handler = InputHandler()
        
        # Generar estrellas de fondo según el modo (solo una vez)
        if USE_DOME_GEOMETRY:
            self.background_stars = self._generate_dome_stars()
        else:
            self.background_stars = [
                (random.uniform(WORLD_MIN*2, WORLD_MAX*2), 
                 random.uniform(0, 15), 
                 random.uniform(WORLD_MIN*2, WORLD_MAX*2))
                for _ in range(NUM_BACKGROUND_STARS)
            ]
        
        # Registrar eventos
        self._register_events()

        # Pre-crear quadrics para esferas
        self.planet_sphere_vbo = create_sphere_vertex_list(radius=1.0, slices=32, stacks=32)

        
        # Variables para cálculo de LST (evitar recalcular)
        self.last_lst_calculation = 0
        self.cached_lst_deg = 0
        self.cached_lst_h = 0
        self.lst_update_interval = 1.0  # Actualizar cada 1 segundo
        
        # Iniciar bucle de actualización
        pyglet.clock.schedule(self.update)

    def _generate_dome_stars(self):
        """Genera estrellas distribuidas en la superficie del domo"""
        import math
        stars = []
        for _ in range(NUM_BACKGROUND_STARS):
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi / 2)
            
            r = DOME_RADIUS * 0.98
            x = r * math.sin(phi) * math.cos(theta)
            z = r * math.sin(phi) * math.sin(theta)
            y = r * math.cos(phi) - 1
            
            stars.append((x, y, z))
        return stars
    
    def _register_events(self):
        """Registra los manejadores de eventos"""
        self.window.on_resize = self.on_resize
        self.window.on_key_press = self.on_key_press
        self.window.on_key_release = self.on_key_release
        self.window.on_text = self.on_text
        self.window.on_mouse_motion = self.on_mouse_motion
        self.window.on_draw = self.on_draw
    
    def on_resize(self, width, height):
        """Maneja el redimensionamiento de la ventana"""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, width/height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED
    
    def on_key_press(self, symbol, modifiers):
        """Maneja las teclas presionadas"""
        if symbol == key.ENTER and modifiers & key.MOD_ALT:
            self.window.set_fullscreen(not self.window.fullscreen)
            return pyglet.event.EVENT_HANDLED
        
        if symbol == key.ESCAPE:
            if self.search_box.active:
                self.search_box.deactivate()
                self.window.set_exclusive_mouse(True)
                return pyglet.event.EVENT_HANDLED
            return
        
        if symbol == key.T and not self.search_box.active:
            self.window.set_exclusive_mouse(False)
            self.search_box.activate()
            return pyglet.event.EVENT_HANDLED

        if symbol == key.B:
            self.bloom.toggle()
            return pyglet.event.EVENT_HANDLED
        
        if self.search_box.active:
            if symbol == key.ENTER:
                if self.tracker.start_tracking(self.search_box.get_text()):
                    self.search_box.deactivate()
                    self.window.set_exclusive_mouse(True)
                else:
                    self.search_box.clear()
            elif symbol == key.BACKSPACE:
                self.search_box.backspace()
            return
        
        if symbol == key.C:
            self.tracker.stop_tracking()
        
        self.input_handler.press_key(symbol)
        return pyglet.event.EVENT_HANDLED
    
    def on_key_release(self, symbol, modifiers):
        """Maneja las teclas soltadas"""
        self.input_handler.release_key(symbol)
    
    def on_text(self, text):
        """Maneja la entrada de texto"""
        if self.search_box.active:
            self.search_box.add_char(text)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Maneja el movimiento del mouse"""
        if not self.search_box.active:
            self.camera.rotate(dx, dy)

    def _calculate_lst_cached(self):
        """Calcula LST con cache para evitar cálculos innecesarios"""
        current_time = time.time()
        
        if current_time - self.last_lst_calculation > self.lst_update_interval:
            now_utc = datetime.now(timezone.utc)
            self.cached_lst_deg, self.cached_lst_h = calculate_lst(
                now_utc, LOCATION_LONGITUDE
            )
            self.last_lst_calculation = current_time
        
        return self.cached_lst_deg, self.cached_lst_h

    def update(self, dt):
        """Actualiza el estado de la aplicación"""
        # Ajustar velocidad según CTRL
        is_slow = self.input_handler.is_ctrl_held()
        self.camera.set_speed_modifier(is_slow)
        
        # Actualizar movimiento de cámara
        self.input_handler.update_camera_movement(self.camera, dt)
        
        # Actualizar movimiento de vector (solo si no está rastreando)
        if not self.tracker.is_tracking():
            self.input_handler.update_vector_movement(self.vector, dt)
        else:
            self.tracker.update_vector_to_target(self.vector)
        
        # Actualizar proyección según FOV
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            self.camera.fov, 
            self.window.width/self.window.height, 
            0.1, 100.0
        )
        glMatrixMode(GL_MODELVIEW)

        yaw, pitch = self.vector.yaw, self.vector.pitch
        
        # Enviar al ESP32
        self.serial_device.send_angles(yaw, pitch)
    
        # Leer del ESP32 o simular lectura con delay
        if not SIMULATE:
            line = self.serial_device.read_data()
            if line:
                msg = self.serial_device.parse_message(line)
                if msg and msg["type"] == "SENS":
                    yaw = msg["yaw"]
                    pitch = msg["pitch"]
                    self.sensor_vector.set_angles(yaw, pitch)
        else:
            # Modo simulado: "seguir" al vector rojo
            current_yaw = self.sensor_vector.yaw
            current_pitch = self.sensor_vector.pitch
            target_yaw = self.vector.yaw
            target_pitch = self.vector.pitch
            
            follow_speed = 0.005
            delta_yaw = (target_yaw - current_yaw + 540) % 360 - 180
            new_yaw = (current_yaw + delta_yaw * follow_speed) % 360
            delta_pitch = target_pitch - current_pitch
            new_pitch = current_pitch + delta_pitch * follow_speed
            
            self.sensor_vector.set_angles(new_yaw, new_pitch)

    def on_draw(self):
        
        """Dibuja la escena"""
        self.window.clear()
        
        # Calcular LST con cache
        lst_deg, lst_h = self._calculate_lst_cached()
        
        # Determinar función de proyección según el modo
        projection_func = None
        projection_kwargs = {}
        
        if USE_DOME_GEOMETRY:
            from astronomy import ra_dec_to_dome
            projection_func = ra_dec_to_dome
            projection_kwargs = {'dome_radius': DOME_RADIUS}
        else:
            from astronomy import ra_dec_to_xyz
            projection_func = ra_dec_to_xyz

        # Actualizar coordenadas solo si es necesario
        if self.coord_cache.should_update(lst_h):
            self.coord_cache.update(lst_h, projection_func, projection_kwargs)
        
        # Usar coordenadas cacheadas
        stars_coords = self.coord_cache.stars_coords
        galaxies_coords = self.coord_cache.galaxies_coords
        planets_coords = self.coord_cache.planets_coords
        moon_coords = self.coord_cache.moon_coords
        
        # Variables para almacenar los datos de los vectores
        vector_data = [None]
        
        # ============================================================
        # FUNCIÓN QUE DIBUJA LA ESCENA COMPLETA (PARA BLOOM)
        # ============================================================
        def render_scene_for_bloom():
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LESS)
            self.camera.apply_view()
            
            # Dibujar entorno SIN ILUMINACIÓN (colores puros)
            glDisable(GL_LIGHTING)
            
            draw_environment(self.camera, self.background_stars, use_dome=USE_DOME_GEOMETRY)
            draw_cardinals()
            
            # ============================================================
            # OBJETOS CELESTIALES - CON ILUMINACIÓN REALISTA
            # ============================================================
            draw_celestial_objects_with_textures(
                stars_coords, galaxies_coords, 
                planets_coords, moon_coords, 
                self.planet_sphere_vbo,
                self.texture_manager,
                self.camera,
                fov=self.camera.fov,
                use_lighting=USE_LIGHTING  # ← ACTIVAR ILUMINACIÓN
            )
        
        # ============================================================
        # RENDERIZAR TODO CON BLOOM
        # ============================================================
        self.bloom.render_with_bloom(
            render_scene_for_bloom, 
            self.window.width, 
            self.window.height
        )
        
        # ============================================================
        # RENDERIZAR VECTORES (SIN BLOOM) - ENCIMA
        # ============================================================
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)  # Los vectores no usan iluminación
        glDisable(GL_TEXTURE_2D)  # Asegurar que texturas estén OFF
        glEnable(GL_DEPTH_TEST)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)  # Restaurar color mask
        
        self.camera.apply_view()
        
        vector_data[0] = self.vector.draw()
        self.sensor_vector.draw(color=(0, 1, 0), crosshair=(0,1,0))
        
        # ============================================================
        # RESTAURAR ESTADO DE OPENGL PARA UI
        # ============================================================
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # ============================================================
        # DIBUJAR UI ENCIMA
        # ============================================================
        draw_crosshair(self.window)
        self.search_box.draw(self.window)
        
        # Obtener los datos del vector
        end_x, end_y, end_z, hit_x, hit_y, hit_z = vector_data[0]
        
        # Detectar objetos apuntados
        pointed_obj = detect_pointed_object_by_vector(
            (hit_x, hit_y, hit_z),
            stars_coords, galaxies_coords, 
            planets_coords, moon_coords
        )
        
        looked_obj = detect_looked_object_by_camera(
            self.camera,
            stars_coords, galaxies_coords,
            planets_coords, moon_coords
        )
        
        # Mostrar información
        info_lines = InfoDisplay.create_info_text(
            self.camera, self.vector,
            self.sensor_vector,
            lst_deg, lst_h,
            self.tracker.get_tracked_object_name(),
            looked_obj,
            self.bloom.user_enabled
        )
        self.text_renderer.draw(self.window, info_lines, self.window.height - 20)
        
        # Mostrar FPS
        self.fps_display.draw()


    def run(self):
        """Inicia la aplicación"""
        pyglet.app.run()

    def on_close(self):
        """Se ejecuta al cerrar la ventana"""
        self.serial_device.close()
        self.window.close()


if __name__ == "__main__":
    app = SkyTrackerApp()
    app.run()