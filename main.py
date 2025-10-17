# main.py
"""
SkyTracker - Aplicación principal
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
    draw_celestial_objects, draw_cardinals, draw_text_2d, CachedTextRenderer
)
from ui import SearchBox, InfoDisplay
from object_detection import (
    detect_pointed_object_by_vector,
    detect_looked_object_by_camera
)
from tracker import ObjectTracker
from input_handler import InputHandler


class SkyTrackerApp:
    """Clase principal de la aplicación SkyTracker"""
    
    def __init__(self):
        # Crear ventana
        self.window = pyglet.window.Window(
            WINDOW_WIDTH, WINDOW_HEIGHT, 
            WINDOW_TITLE, 
            resizable=True
        )
        self.window.set_minimum_size(400, 300)
        self.window.set_exclusive_mouse(True)
        
        # FPS display
        self.fps_display = pyglet.window.FPSDisplay(window=self.window)

         # Renderer de texto cacheado
        self.text_renderer = CachedTextRenderer()
        
        # Componentes
        self.camera = Camera()
        self.vector = PointerVector()
        self.search_box = SearchBox()
        self.tracker = ObjectTracker()
        self.input_handler = InputHandler()
        
        # Generar estrellas de fondo
        self.background_stars = [
            (random.uniform(WORLD_MIN*2, WORLD_MAX*2), 
             random.uniform(0, 15), 
             random.uniform(WORLD_MIN*2, WORLD_MAX*2))
            for _ in range(NUM_BACKGROUND_STARS)
        ]
        
        # Registrar eventos
        self._register_events()

        # Pre-crear quadrics para esferas
        self.sphere_quad = gluNewQuadric()
        
        # Iniciar bucle de actualización
        pyglet.clock.schedule(self.update)
    
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
        # Alt+Enter para fullscreen
        if symbol == key.ENTER and modifiers & key.MOD_ALT:
            self.window.set_fullscreen(not self.window.fullscreen)
            return pyglet.event.EVENT_HANDLED
        
        # ESC para cerrar búsqueda o salir
        if symbol == key.ESCAPE:
            if self.search_box.active:
                self.search_box.deactivate()
                return pyglet.event.EVENT_HANDLED
            # Si no hay búsqueda activa, dejar que ESC cierre la app
            return
        
        # T para abrir búsqueda
        if symbol == key.T and not self.search_box.active:
            self.search_box.activate()
            return pyglet.event.EVENT_HANDLED
        
        # Si búsqueda está activa
        if self.search_box.active:
            if symbol == key.ENTER:
                # Intentar rastrear el objeto buscado
                if self.tracker.start_tracking(self.search_box.get_text()):
                    self.search_box.deactivate()
                else:
                    self.search_box.clear()
            elif symbol == key.BACKSPACE:
                self.search_box.backspace()
            return
        
        # C para cancelar rastreo
        if symbol == key.C:
            self.tracker.stop_tracking()
        
        # Registrar tecla presionada
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
            # Actualizar vector para seguir el objeto
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
    
    def on_draw(self):
        """Dibuja la escena"""
        self.window.clear()
        glEnable(GL_DEPTH_TEST)
        
        # Aplicar vista de cámara
        self.camera.apply_view()
        
        # Calcular LST actual
        now_utc = datetime.now(timezone.utc)
        lst_deg, lst_h = calculate_lst(now_utc, LOCATION_LONGITUDE)
        
        
        # Importar la función correcta según el modo
        if USE_DOME:
            from astronomy import ra_dec_to_dome as projection_func
            projection_kwargs = {'dome_radius': DOME_RADIUS}
        else:
            from astronomy import ra_dec_to_xyz as projection_func
            projection_kwargs = {}
            
        # Proyectar objetos celestes
        stars_coords = [
            (name, *projection_func(ra, dec, lst_h, **projection_kwargs))
            for name, ra, dec in REAL_STARS
        ]
        
        galaxies_coords = [
            (name, *projection_func(ra, dec, lst_h, **projection_kwargs))
            for name, ra, dec in GALAXIES
        ]
        
        planets_coords = [
            (name, *projection_func(ra, dec, lst_h, **projection_kwargs))
            for name, ra, dec in PLANETS
        ]
        
        moon_coords = projection_func(*MOON_RA_DEC, lst_h, **projection_kwargs)
        
        moon_coords = ra_dec_to_xyz(*MOON_RA_DEC, lst_h)
        
        # Dibujar escena
        draw_environment(self.background_stars, use_dome=USE_DOME)
        draw_celestial_objects(
            stars_coords, galaxies_coords, 
            planets_coords, moon_coords, self.sphere_quad
        )
        draw_cardinals()
        
        # Dibujar vector y obtener punto de impacto
        end_x, end_y, end_z, hit_x, hit_y, hit_z = self.vector.draw()
        
        # Dibujar UI
        draw_crosshair(self.window)
        self.search_box.draw(self.window)
        
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
            lst_deg, lst_h,
            self.tracker.get_tracked_object_name(),
            looked_obj
        )
        self.text_renderer.draw(self.window, info_lines, self.window.height - 20)
        
        # Mostrar FPS
        self.fps_display.draw()
    
    def run(self):
        """Inicia la aplicación"""
        pyglet.app.run()


if __name__ == "__main__":
    app = SkyTrackerApp()
    app.run()
