# tracker.py
"""
Sistema de rastreo de objetos celestes
"""
from datetime import datetime, timezone
from shared.calculations.astronomy import calculate_lst, ra_dec_to_xyz, calculate_vector_angles
from shared.celestial_data import get_all_celestial_objects
from config import LOCATION_LONGITUDE


class ObjectTracker:
    """Clase para gestionar el rastreo de objetos celestes"""
    
    def __init__(self):
        self.tracking_object = None
        self.celestial_objects = get_all_celestial_objects()
    
    def start_tracking(self, object_name):
        """Inicia el rastreo de un objeto"""
        obj_lower = object_name.lower().strip()
        if obj_lower in self.celestial_objects:
            self.tracking_object = object_name.strip()
            return True
        return False
    
    def stop_tracking(self):
        """Detiene el rastreo"""
        self.tracking_object = None
    
    def is_tracking(self):
        """Verifica si está rastreando algún objeto"""
        return self.tracking_object is not None
    
    def get_tracked_object_name(self):
        """Retorna el nombre del objeto rastreado"""
        return self.tracking_object
    
    def update_vector_to_target(self, vector):
        """
        Actualiza el vector para apuntar al objeto rastreado
        
        Args:
            vector: objeto PointerVector a actualizar
        
        Returns:
            bool: True si se actualizó, False si no hay objeto rastreado
        """
        if not self.tracking_object:
            return False
        
        obj_lower = self.tracking_object.lower()
        if obj_lower not in self.celestial_objects:
            return False
        
        # Obtener coordenadas RA/DEC del objeto
        obj_data = self.celestial_objects[obj_lower]
        ra_h = obj_data['ra_hours']
        dec_deg = obj_data['dec_degrees']
        size = obj_data.get('size', 1.0)
        color = obj_data.get('color', [1.0, 1.0, 1.0])
        
        # Calcular LST actual
        now_utc = datetime.now(timezone.utc)
        lst_deg, lst_h = calculate_lst(now_utc, LOCATION_LONGITUDE)
        
        # Convertir a coordenadas 3D
        target_x, target_y, target_z = ra_dec_to_xyz(ra_h, dec_deg, lst_h)
        
        # Calcular ángulos para apuntar al objeto
        yaw, pitch = calculate_vector_angles(
            target_x, target_y, target_z,
            vector.base_x, vector.base_y, vector.base_z
        )
        
        # Actualizar vector
        vector.yaw = yaw
        vector.pitch = pitch
        
        return True