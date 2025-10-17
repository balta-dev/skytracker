# utils.py
"""
Funciones utilitarias generales
"""
import random
from config import WORLD_MIN, WORLD_MAX, NUM_BACKGROUND_STARS


def generate_background_stars(num_stars=NUM_BACKGROUND_STARS):
    """
    Genera coordenadas aleatorias para estrellas de fondo
    
    Args:
        num_stars: cantidad de estrellas a generar
    
    Returns:
        list: lista de tuplas (x, y, z) con coordenadas
    """
    stars = []
    for _ in range(num_stars):
        x = random.uniform(WORLD_MIN * 2, WORLD_MAX * 2)
        y = random.uniform(0, 15)
        z = random.uniform(WORLD_MIN * 2, WORLD_MAX * 2)
        stars.append((x, y, z))
    return stars


def clamp(value, min_value, max_value):
    """
    Limita un valor entre un mínimo y máximo
    
    Args:
        value: valor a limitar
        min_value: valor mínimo
        max_value: valor máximo
    
    Returns:
        float: valor limitado
    """
    return max(min_value, min(value, max_value))