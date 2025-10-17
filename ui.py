# ui.py
"""
Interfaz de usuario: búsqueda y elementos de información
"""
import pyglet
from pyglet.gl import *


class SearchBox:
    """Clase para gestionar el cuadro de búsqueda de objetos"""
    
    def __init__(self):
        self.active = False
        self.text = ""
    
    def activate(self):
        """Activa el cuadro de búsqueda"""
        self.active = True
        self.text = ""
    
    def deactivate(self):
        """Desactiva el cuadro de búsqueda"""
        self.active = False
        self.text = ""
    
    def add_char(self, char):
        """Agrega un carácter al texto de búsqueda"""
        if len(self.text) < 30 and char.isprintable() and (char.isalnum() or char.isspace()):
            self.text += char
    
    def backspace(self):
        """Elimina el último carácter"""
        self.text = self.text[:-1]
    
    def get_text(self):
        """Retorna el texto actual"""
        return self.text.strip()
    
    def clear(self):
        """Limpia el texto"""
        self.text = ""
    
    def draw(self, window):
        """Dibuja el cuadro de búsqueda"""
        if not self.active:
            return
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, window.width, 0, window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Dimensiones y posición del cuadro
        box_width = 400
        box_height = 100
        box_x = window.width - 550
        box_y = window.height - 150
        
        # Cuadro de fondo
        glColor4f(0.0, 0.0, 0.0, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(box_x, box_y)
        glVertex2f(box_x + box_width, box_y)
        glVertex2f(box_x + box_width, box_y + box_height)
        glVertex2f(box_x, box_y + box_height)
        glEnd()
        
        # Borde
        glColor3f(0.0, 1.0, 1.0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(box_x, box_y)
        glVertex2f(box_x + box_width, box_y)
        glVertex2f(box_x + box_width, box_y + box_height)
        glVertex2f(box_x, box_y + box_height)
        glEnd()
        
        # Título
        title = pyglet.text.Label(
            "Buscar objeto celeste:",
            x=box_x + 10, y=box_y + 70,
            color=(255, 255, 255, 255),
            font_size=12
        )
        title.draw()
        
        # Texto de búsqueda
        search_display = pyglet.text.Label(
            self.text + "_",
            x=box_x + 10, y=box_y + 40,
            color=(0, 255, 255, 255),
            font_size=14,
            bold=True
        )
        search_display.draw()
        
        # Ayuda
        help_text = pyglet.text.Label(
            "ENTER: buscar | ESC: cancelar",
            x=box_x + 10, y=box_y + 10,
            color=(200, 200, 200, 255),
            font_size=10
        )
        help_text.draw()
        
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


class InfoDisplay:
    """Clase para gestionar la información en pantalla"""
    
    @staticmethod
    def create_info_text(camera, vector, lst_deg, lst_h, tracking_obj, looked_obj):
        """Crea las líneas de información a mostrar"""
        lines = [
            f"CÁMARA - Yaw: {camera.yaw:.1f}° Pitch: {camera.pitch:.1f}°",
            f"VECTOR - Yaw: {vector.yaw:.1f}° Pitch: {vector.pitch:.1f}°",
            f"LST: {lst_deg:.2f}° ({lst_h:.2f}h)",
            f"Rastreando: {tracking_obj if tracking_obj else 'ninguno'}",
            f"Apuntando con mouse: {looked_obj if looked_obj else 'ninguno'}",
            "",
            "Objetos disponibles: Sirius, Betelgeuse, Rigel, Vega, Antares,",
            "Polaris, Altair, Deneb, Spica, Arcturus, Luna, M31 (Andromeda), M81, M51,",
            "Mercurio, Venus, Marte, Jupiter, Saturno"
        ]
        return lines