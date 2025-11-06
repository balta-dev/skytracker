# ui.py
"""
Interfaz de usuario: búsqueda y elementos de información - OPTIMIZADO
"""
import pyglet
from pyglet.gl import *

class LookAtDisplay:
    """Muestra el objeto al que se está apuntando con el mouse"""
    
    def __init__(self):
        self.current_object = None
        self.label = pyglet.text.Label(
            "",
            x=0, y=0,
            anchor_x='center',
            anchor_y='bottom',
            color=(0, 255, 255, 255),
            font_size=14,
            bold=True
        )
    
    def update(self, object_name):
        """Actualiza el objeto mostrado"""
        self.current_object = object_name
    
    def draw(self, window):
        """Dibuja el label sin fondo"""
        if not self.current_object:
            return
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, window.width, 0, window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        cx = window.width // 2
        cy = window.height // 2
        offset = 30
        
        self.label.text = self.current_object
        self.label.x = cx
        self.label.y = cy + offset
        
        # Sin fondo - directamente dibuja el label
        self.label.draw()
        
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

class SearchBox:
    """Clase para gestionar el cuadro de búsqueda de objetos - OPTIMIZADA"""
    
    def __init__(self):
        self.active = False
        self.text = ""
        
        # Pre-crear labels para evitar recreación
        self.title_label = pyglet.text.Label(
            "Buscar objeto celeste:",
            x=0, y=0,
            color=(255, 255, 255, 255),
            font_size=12
        )
        
        self.search_label = pyglet.text.Label(
            "",
            x=0, y=0,
            color=(0, 255, 255, 255),
            font_size=14,
            bold=True
        )
        
        self.help_label = pyglet.text.Label(
            "ENTER: buscar | ESC: cancelar",
            x=0, y=0,
            color=(200, 200, 200, 255),
            font_size=10
        )
        
        # Batch para renderizar todo junto
        self.batch = pyglet.graphics.Batch()
        
        # Recrear labels con el batch
        self._recreate_labels_with_batch()
    
    def _recreate_labels_with_batch(self):
        """Recrea los labels usando el batch para mejor performance"""
        self.title_label.delete()
        self.search_label.delete()
        self.help_label.delete()
        
        self.title_label = pyglet.text.Label(
            "Buscar objeto celeste:",
            x=0, y=0,
            color=(255, 255, 255, 255),
            font_size=12,
            batch=self.batch
        )
        
        self.search_label = pyglet.text.Label(
            "",
            x=0, y=0,
            color=(0, 255, 255, 255),
            font_size=14,
            bold=True,
            batch=self.batch
        )
        
        self.help_label = pyglet.text.Label(
            "ENTER: buscar | ESC: cancelar",
            x=0, y=0,
            color=(200, 200, 200, 255),
            font_size=10,
            batch=self.batch
        )
    
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
        """Dibuja el cuadro de búsqueda - OPTIMIZADO"""
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
        
        # Actualizar posiciones de los labels
        self.title_label.x = box_x + 10
        self.title_label.y = box_y + 70
        
        self.search_label.text = self.text + "_"
        self.search_label.x = box_x + 10
        self.search_label.y = box_y + 40
        
        self.help_label.x = box_x + 10
        self.help_label.y = box_y + 10
        
        # Dibujar todos los labels en un solo batch
        self.batch.draw()
        
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


class InfoDisplay:
    """Clase para gestionar la información en pantalla"""
    
    # Cache de líneas de objetos disponibles (no cambian nunca)
    _static_lines_cache = None
    # IP del servidor (se setea una vez)
    _server_ip = None
    
    @classmethod
    def set_server_ip(cls, ip):
        """Setea la IP del servidor (se llama una sola vez al inicio)"""
        cls._server_ip = ip
    
    @classmethod
    def _get_static_lines(cls):
        """Obtiene las líneas estáticas (se cachean una sola vez)"""
        if cls._static_lines_cache is None:
            lines = []
            
            # Agregar IP del servidor si está disponible
            if cls._server_ip:
                lines.append(f"SERVIDOR TCP: {cls._server_ip}:12345")
                lines.append("")
            
            lines.extend([
                "Objetos disponibles:",
                "  * Estrellas:",
                "    Acrux, Aldebaran, Hadar, Adhara, Castor, Gacrux,",
                "    Bellatrix, Elnath, Saiph, Regulus, Sirius,",
                "    Betelgeuse, Rigel, Vega, Antares, Polaris,",
                "    Altair, Deneb, Spica, Arcturus, Canopus,",
                "    Achernar, Alpha Centauri, Fomalhaut, Diphda,",
                "    Mintaka, Alnilam, Alnitak, Electra, Merope,",
                "    Alcyone, Atlas, Pleione, Taygeta, Maia",
                "",
                "  * Galaxias: LMC, SMC, M31, M33, M81, M51",
                "  * Sistema Solar:",
                "    - Planetas: Mercurio, Venus,",
                "      Marte, Jupiter, Saturno,",
                "    - Sol",
                "    - Luna"
            ])
            
            cls._static_lines_cache = lines
        return cls._static_lines_cache
    
    @staticmethod
    def create_info_text(camera, vector, sensor_vector, lst_deg, lst_h, 
                        tracking_obj, looked_obj, bloom_enabled):
        """Crea las líneas de información a mostrar - OPTIMIZADO"""
        
        # Líneas dinámicas (cambian frecuentemente)
        dynamic_lines = [
            f"CÁMARA - Yaw: {camera.yaw:.1f}° Pitch: {camera.pitch:.1f}°",
            f"VECTOR - Yaw: {vector.yaw:.1f}° Pitch: {vector.pitch:.1f}°",
            f"FEEDBACK - Yaw: {sensor_vector.yaw:.1f}° Pitch: {sensor_vector.pitch:.1f}°",
            f"LST: {lst_deg:.2f}° ({lst_h:.2f}h)",
            f"Bloom: {'ON' if bloom_enabled else 'OFF'} [B]",
            f"Rastreando: {tracking_obj if tracking_obj else 'ninguno'}",
            f"Apuntando con mouse: {looked_obj if looked_obj else 'ninguno'}",
            ""
        ]
        
        # Combinar con líneas estáticas cacheadas
        return dynamic_lines + InfoDisplay._get_static_lines()