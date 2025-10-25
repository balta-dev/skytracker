# object_detection.py
"""
Detección de objetos celestes apuntados por cámara o vector
"""
import math
from config import (
    THRESHOLD_OBJECT, THRESHOLD_MOON, 
    THRESHOLD_PLANET, THRESHOLD_CAMERA
)


def detect_pointed_object_by_vector(hit_coords, stars_coords, galaxies_coords, 
                                     planets_coords, moon_coords):
    """
    Detecta qué objeto está siendo apuntado por el vector
    
    Args:
        hit_coords: tupla (x, y, z) del punto de impacto del vector
        stars_coords: lista de coordenadas de estrellas
        galaxies_coords: lista de coordenadas de galaxias
        planets_coords: lista de coordenadas de planetas
        moon_coords: tupla (x, y, z) de la luna
    
    Returns:
        str: nombre del objeto detectado o None
    """
    if hit_coords[0] is None:
        return None
    
    hit_x, hit_y, hit_z = hit_coords
    
    # Verificar estrellas
    for name, x, y, z in stars_coords:
        dist = math.sqrt((hit_x - x)**2 + (hit_y - y)**2 + (hit_z - z)**2)
        if dist < THRESHOLD_OBJECT:
            return name
    
    # Verificar galaxias
    for name, x, y, z in galaxies_coords:
        dist = math.sqrt((hit_x - x)**2 + (hit_y - y)**2 + (hit_z - z)**2)
        if dist < THRESHOLD_OBJECT:
            return name
    
    # Verificar planetas
    for name, x, y, z in planets_coords:
        dist = math.sqrt((hit_x - x)**2 + (hit_y - y)**2 + (hit_z - z)**2)
        if dist < THRESHOLD_PLANET:
            return name
    
    # Verificar luna
    dist_moon = math.sqrt(
        (hit_x - moon_coords[0])**2 + 
        (hit_y - moon_coords[1])**2 + 
        (hit_z - moon_coords[2])**2
    )
    if dist_moon < THRESHOLD_MOON:
        return "Luna"
    
    return None


def detect_looked_object_by_camera(camera, stars_coords, galaxies_coords, 
                                    planets_coords, moon_coords):
    """
    Detecta qué objeto está siendo mirado por la cámara
    
    Args:
        camera: objeto Camera
        stars_coords: lista de coordenadas de estrellas
        galaxies_coords: lista de coordenadas de galaxias
        planets_coords: lista de coordenadas de planetas
        moon_coords: tupla (x, y, z) de la luna
    
    Returns:
        str: nombre del objeto detectado o None
    """
    cam_dx, cam_dy, cam_dz = camera.get_direction()
    
    def check_object(coords, threshold):
        """Verifica si algún objeto está siendo mirado"""
        closest_name = None
        closest_angle = 999
        
        for name, x, y, z in coords:
            # Vector desde cámara al objeto
            vx = x - camera.x
            vy = y - camera.y
            vz = z - camera.z
            norm = math.sqrt(vx*vx + vy*vy + vz*vz)
            
            if norm == 0:
                continue
            
            vx /= norm
            vy /= norm
            vz /= norm
            
            # Producto punto para calcular ángulo
            dot = vx*cam_dx + vy*cam_dy + vz*cam_dz
            dot = max(-1, min(1, dot))  # clamp
            angle = math.degrees(math.acos(dot))
            
            if angle < threshold and angle < closest_angle:
                closest_angle = angle
                closest_name = name
        
        return closest_name
    
    # Verificar estrellas
    looked = check_object(stars_coords, THRESHOLD_CAMERA)
    if looked:
        return looked
    
    # Verificar galaxias
    looked = check_object(galaxies_coords, THRESHOLD_CAMERA)
    if looked:
        return looked
    
    # Verificar planetas
    looked = check_object(planets_coords, THRESHOLD_CAMERA)
    if looked:
        return looked
    
    # Verificar luna
    vx = moon_coords[0] - camera.x
    vy = moon_coords[1] - camera.y
    vz = moon_coords[2] - camera.z
    norm = math.sqrt(vx*vx + vy*vy + vz*vz)
    
    if norm > 0:
        vx /= norm
        vy /= norm
        vz /= norm
        dot = vx*cam_dx + vy*cam_dy + vz*cam_dz
        dot = max(-1, min(1, dot))
        angle = math.degrees(math.acos(dot))
        
        if angle < THRESHOLD_CAMERA:
            return "Luna"
    
    return None