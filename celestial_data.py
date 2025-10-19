# celestial_data.py
"""
Cargador de datos de objetos celestes desde JSON
"""
import json
import os


class CelestialDataLoader:
    """Carga y gestiona datos de objetos celestes desde JSON"""
    
    def __init__(self, json_file='celestial_data.json'):
        self.json_file = json_file
        self.data = self._load_json()
    
    def _load_json(self):
        """Carga el archivo JSON"""
        try:
            if not os.path.exists(self.json_file):
                print(f"WARNING: {self.json_file} no encontrado, usando valores por defecto")
                return self._get_default_data()
            
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR cargando {self.json_file}: {e}")
            return self._get_default_data()
    
    def _get_default_data(self):
        """Retorna datos por defecto si falla la carga"""
        return {
            "stars": [],
            "galaxies": [],
            "planets": [],
            "moon": {"ra_hours": 0, "dec_degrees": 0},
            "metadata": {}
        }
    
    def get_stars(self):
        """Retorna lista de tuplas (nombre, ra_h, dec_deg)"""
        return [(s['name'], s['ra_hours'], s['dec_degrees']) 
                for s in self.data.get('stars', [])]
    
    def get_galaxies(self):
        """Retorna lista de tuplas (nombre, ra_h, dec_deg)"""
        return [(g['name'], g['ra_hours'], g['dec_degrees']) 
                for g in self.data.get('galaxies', [])]
    
    def get_planets(self):
        """Retorna lista de tuplas (nombre, ra_h, dec_deg)"""
        return [(p['name'], p['ra_hours'], p['dec_degrees']) 
                for p in self.data.get('planets', [])]
    
    def get_moon(self):
        """Retorna tupla (ra_h, dec_deg)"""
        moon = self.data.get('moon', {})
        return (moon.get('ra_hours', 0), moon.get('dec_degrees', 0))
    
    def update_planets(self, planets_dict):
        """
        Actualiza las coordenadas de los planetas
        
        Args:
            planets_dict: dict con formato {'Mercurio': (ra_h, dec_deg), ...}
        """
        from datetime import datetime, timezone
        
        for planet in self.data.get('planets', []):
            name = planet['name']
            if name in planets_dict:
                ra, dec = planets_dict[name]
                planet['ra_hours'] = ra
                planet['dec_degrees'] = dec
                planet['last_update'] = datetime.now(timezone.utc).isoformat()
        
        self._save_json()
    
    def update_moon(self, ra_hours, dec_degrees):
        """Actualiza las coordenadas de la Luna"""
        from datetime import datetime, timezone
        
        self.data['moon']['ra_hours'] = ra_hours
        self.data['moon']['dec_degrees'] = dec_degrees
        self.data['moon']['last_update'] = datetime.now(timezone.utc).isoformat()
        
        self._save_json()
    
    def _save_json(self):
        """Guarda los datos al archivo JSON"""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"ERROR guardando {self.json_file}: {e}")
            return False
    
    def get_all_objects_dict(self):
        """
        Retorna diccionario con todos los objetos para busqueda
        Las claves son nombres en minusculas
        """
        objects = {}
        
        for name, ra, dec in self.get_stars():
            objects[name.lower()] = (ra, dec)
        
        for name, ra, dec in self.get_galaxies():
            objects[name.lower()] = (ra, dec)
        
        for name, ra, dec in self.get_planets():
            objects[name.lower()] = (ra, dec)
        
        moon_coords = self.get_moon()
        objects['luna'] = moon_coords
        objects['moon'] = moon_coords
        
        return objects
    
    def get_object_list_text(self):
        """Retorna texto con la lista de objetos disponibles"""
        stars = ", ".join([name for name, _, _ in self.get_stars()])
        galaxies = ", ".join([name for name, _, _ in self.get_galaxies()])
        planets = ", ".join([name for name, _, _ in self.get_planets()])
        
        return f"{stars}, Luna, {galaxies}, {planets}"


# Instancia global para compatibilidad con codigo existente
_loader = CelestialDataLoader()

# Variables globales para retrocompatibilidad
REAL_STARS = _loader.get_stars()
GALAXIES = _loader.get_galaxies()
PLANETS = _loader.get_planets()
MOON_RA_DEC = _loader.get_moon()


def get_all_celestial_objects():
    """Retorna diccionario con todos los objetos celestes"""
    return _loader.get_all_objects_dict()


def get_object_list_text():
    """Retorna el texto con la lista de objetos disponibles"""
    return _loader.get_object_list_text()


def reload_data():
    """Recarga los datos desde el JSON"""
    global _loader, REAL_STARS, GALAXIES, PLANETS, MOON_RA_DEC
    _loader = CelestialDataLoader()
    REAL_STARS = _loader.get_stars()
    GALAXIES = _loader.get_galaxies()
    PLANETS = _loader.get_planets()
    MOON_RA_DEC = _loader.get_moon()