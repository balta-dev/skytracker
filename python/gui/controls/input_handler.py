# input_handler.py
"""
Manejo de entrada del teclado y mouse
"""
from pyglet.window import key


class InputHandler:
    """Clase para gestionar la entrada de teclado y mouse"""
    
    def __init__(self):
        self.keys_held = set()
    
    def press_key(self, symbol):
        """Registra que una tecla fue presionada"""
        self.keys_held.add(symbol)
    
    def release_key(self, symbol):
        """Registra que una tecla fue soltada"""
        self.keys_held.discard(symbol)
    
    def is_key_held(self, symbol):
        """Verifica si una tecla está presionada"""
        return symbol in self.keys_held
    
    def is_ctrl_held(self):
        """Verifica si CTRL está presionado"""
        return key.LCTRL in self.keys_held or key.RCTRL in self.keys_held
    
    def is_shift_held(self):
        """Verifica si SHIFT está presionado"""
        return key.LSHIFT in self.keys_held or key.RSHIFT in self.keys_held
    
    def update_camera_movement(self, camera, dt):
        """
        Actualiza la posición de la cámara según las teclas presionadas
        
        Args:
            camera: objeto Camera
            dt: delta time
        """
        speed = camera.speed
        
        # Movimiento horizontal (WASD)
        if self.is_key_held(key.W):
            camera.move_forward(speed)
        if self.is_key_held(key.S):
            camera.move_backward(speed)
        if self.is_key_held(key.A):
            camera.move_left(speed)
        if self.is_key_held(key.D):
            camera.move_right(speed)
        
        # Movimiento vertical
        if self.is_key_held(key.SPACE):
            camera.move_up(speed)
        if self.is_shift_held():
            camera.move_down(speed)
        
        # Zoom
        zoom_speed = 20.0 * dt * 10
        if self.is_key_held(key.Z):
            camera.adjust_zoom(-zoom_speed)
        if self.is_key_held(key.X):
            camera.adjust_zoom(zoom_speed)
    
    def update_vector_movement(self, vector, dt):
        """
        Actualiza la rotación del vector según las teclas presionadas
        
        Args:
            vector: objeto PointerVector
            dt: delta time
        """
        vec_speed = 0.1 if self.is_ctrl_held() else 1.0
        
        if self.is_key_held(key.UP):
            vector.rotate(0, vec_speed)
        if self.is_key_held(key.DOWN):
            vector.rotate(0, -vec_speed)
        if self.is_key_held(key.LEFT):
            vector.rotate(vec_speed, 0)
        if self.is_key_held(key.RIGHT):
            vector.rotate(-vec_speed, 0)