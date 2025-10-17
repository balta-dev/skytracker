# astronomy.py
"""
Funciones astronómicas para cálculos de coordenadas
"""
import math
from datetime import datetime, timezone
from config import LOCATION_LONGITUDE, WORLD_SCALE


def calculate_lst(now_utc, longitude_deg):
    """
    Calcula Local Sidereal Time para una fecha UTC y longitud en grados
    
    Args:
        now_utc: datetime object en UTC
        longitude_deg: longitud del observador en grados
    
    Returns:
        tuple: (LST en grados, LST en horas)
    """
    Y, M, D = now_utc.year, now_utc.month, now_utc.day
    H, MN, S = now_utc.hour, now_utc.minute, now_utc.second + now_utc.microsecond/1e6

    # Julian Date UTC
    if M <= 2:
        Y -= 1
        M += 12
    A = int(Y/100)
    B = 2 - A + int(A/4)
    JD = int(365.25*(Y + 4716)) + int(30.6001*(M + 1)) + D + B - 1524.5
    JD += (H + MN/60 + S/3600)/24  # fracción de día

    # Tiempo juliano en siglos desde J2000.0
    T = (JD - 2451545.0)/36525.0

    # Greenwich Mean Sidereal Time en grados
    GMST = 280.46061837 + 360.98564736629*(JD - 2451545.0) + 0.000387933*T**2 - T**3/38710000
    GMST = GMST % 360

    # Local Sidereal Time
    LST_deg = (GMST + longitude_deg) % 360
    LST_h = LST_deg / 15

    return LST_deg, LST_h


def ra_dec_to_xyz(ra_h, dec_deg, lst_h, lat_deg=LOCATION_LONGITUDE):
    """
    Convierte coordenadas RA/DEC a coordenadas 3D cartesianas
    
    Args:
        ra_h: Ascensión Recta en horas
        dec_deg: Declinación en grados
        lst_h: Local Sidereal Time en horas
        lat_deg: Latitud del observador en grados
    
    Returns:
        tuple: (x, y, z) coordenadas en el espacio 3D
    """
    # Hour Angle
    ha_h = lst_h - ra_h
    ha_deg = ha_h * 15
    ha_rad = math.radians(ha_deg)
    dec_rad = math.radians(dec_deg)
    lat_rad = math.radians(lat_deg)

    # Altura (elevación) y Acimut
    sin_alt = math.sin(dec_rad)*math.sin(lat_rad) + math.cos(dec_rad)*math.cos(lat_rad)*math.cos(ha_rad)
    alt_rad = math.asin(sin_alt)

    cos_az = (math.sin(dec_rad) - math.sin(alt_rad)*math.sin(lat_rad)) / (math.cos(alt_rad)*math.cos(lat_rad))
    az_rad = math.acos(max(min(cos_az, 1.0), -1.0))  # proteger de errores numéricos

    # Ajuste de azimut según el signo del seno del HA
    if math.sin(ha_rad) > 0:
        az_rad = 2*math.pi - az_rad

    # Proyección a 3D
    x = math.cos(alt_rad) * math.sin(az_rad)
    y = math.sin(alt_rad)
    z = -math.cos(alt_rad) * math.cos(az_rad)

    # Escalar para que llegue a ±WORLD_SCALE
    factor = WORLD_SCALE / max(abs(x), abs(y), abs(z))
    return x*factor, y*factor, z*factor


def ra_dec_to_dome(ra_h, dec_deg, lst_h, lat_deg=LOCATION_LONGITUDE, dome_radius=30.0):
    """
    Convierte coordenadas RA/DEC a coordenadas 3D sobre la superficie de un domo
    
    Args:
        ra_h: Ascensión Recta en horas
        dec_deg: Declinación en grados
        lst_h: Local Sidereal Time en horas
        lat_deg: Latitud del observador en grados
        dome_radius: Radio del domo
    
    Returns:
        tuple: (x, y, z) coordenadas sobre la superficie del domo
    """
    # Hour Angle
    ha_h = lst_h - ra_h
    ha_deg = ha_h * 15
    ha_rad = math.radians(ha_deg)
    dec_rad = math.radians(dec_deg)
    lat_rad = math.radians(lat_deg)

    # Altura (elevación) y Acimut
    sin_alt = math.sin(dec_rad)*math.sin(lat_rad) + math.cos(dec_rad)*math.cos(lat_rad)*math.cos(ha_rad)
    alt_rad = math.asin(sin_alt)

    cos_az = (math.sin(dec_rad) - math.sin(alt_rad)*math.sin(lat_rad)) / (math.cos(alt_rad)*math.cos(lat_rad))
    az_rad = math.acos(max(min(cos_az, 1.0), -1.0))

    # Ajuste de azimut
    if math.sin(ha_rad) > 0:
        az_rad = 2*math.pi - az_rad

    # Si el objeto está debajo del horizonte, no lo mostramos (o lo ponemos en el horizonte)
    if alt_rad < 0:
        alt_rad = 0
    
    # Convertir a coordenadas esféricas del domo
    # alt_rad = 0 -> horizonte, alt_rad = pi/2 -> cenit
    # Mapear altitud [0, pi/2] a ángulo polar [pi/2, 0]
    phi = math.pi/2 - alt_rad  # ángulo desde el polo (cenit)
    theta = az_rad  # azimut
    
    # Coordenadas cartesianas en el domo
    x = dome_radius * math.sin(phi) * math.cos(theta)
    z = dome_radius * math.sin(phi) * math.sin(theta)
    y = dome_radius * math.cos(phi) - 1  # -1 para que el suelo esté en y=-1
    
    return x, y, z


def calculate_vector_angles(target_x, target_y, target_z, base_x, base_y, base_z):
    """
    Calcula los ángulos yaw y pitch necesarios para apuntar desde la base hacia el objetivo
    
    Args:
        target_x, target_y, target_z: coordenadas del objetivo
        base_x, base_y, base_z: coordenadas de la base del vector
    
    Returns:
        tuple: (yaw, pitch) en grados
    """
    dx = target_x - base_x
    dy = target_y - base_y
    dz = target_z - base_z
    
    # Calcular pitch (elevación)
    horizontal_dist = math.sqrt(dx**2 + dz**2)
    pitch = math.degrees(math.atan2(dy, horizontal_dist))
    
    # Calcular yaw (azimut)
    yaw = math.degrees(math.atan2(dx, dz))
    
    return yaw, pitch