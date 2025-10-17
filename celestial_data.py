# celestial_data.py
"""
Datos de objetos celestes (estrellas, planetas, galaxias)
RA en horas, DEC en grados
"""

# Estrellas principales con coordenadas RA/DEC
REAL_STARS = [
    ("Sirius", 6.752, -16.72),
    ("Betelgeuse", 5.919, 7.407),
    ("Rigel", 5.243, -8.201),
    ("Vega", 18.615, 38.78),
    ("Antares", 16.490, -26.43),
    ("Polaris", 2.530, 89.264),
    ("Altair", 19.846, 8.868),
    ("Deneb", 20.690, 45.280),
    ("Spica", 13.420, -11.161),
    ("Arcturus", 14.261, 19.182),
]

# Galaxias con coordenadas RA/DEC
GALAXIES = [
    ("M31", 0.712, 41.27),      # Galaxia de Andrómeda
    ("M81", 9.927, 69.07),       # Galaxia de Bode
    ("M51", 13.497, 47.20),      # Galaxia del Remolino
]

# Planetas con coordenadas aproximadas
PLANETS = [
    ("Mercurio", 14.7047, -17.6831),   
    ("Venus", 12.2089, 0.2944),        
    ("Marte", 14.886, -16.800),      
    ("Jupiter", 3.2841, 16.7892),      
    ("Saturno", 23.1562, -8.9473)
]

# Coordenadas de la Luna (simplificado)
MOON_RA_DEC = (10.684, 13.0)

def get_all_celestial_objects():
    """
    Retorna un diccionario con todos los objetos celestes
    Las claves son nombres en minúsculas para búsqueda
    """
    celestial_objects = {}
    
    for name, ra, dec in REAL_STARS:
        celestial_objects[name.lower()] = (ra, dec)
    
    for name, ra, dec in GALAXIES:
        celestial_objects[name.lower()] = (ra, dec)
    
    for name, ra, dec in PLANETS:
        celestial_objects[name.lower()] = (ra, dec)
    
    celestial_objects["luna"] = MOON_RA_DEC
    celestial_objects["moon"] = MOON_RA_DEC
    
    return celestial_objects

def get_object_list_text():
    """
    Retorna el texto con la lista de objetos disponibles
    """
    stars = ", ".join([name for name, _, _ in REAL_STARS])
    galaxies = ", ".join([name for name, _, _ in GALAXIES])
    planets = ", ".join([name for name, _, _ in PLANETS])
    
    return f"{stars}, Luna, {galaxies}, {planets}"
