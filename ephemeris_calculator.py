#!/usr/bin/env python3
# ephemeris_calculator.py
"""
Calcula posiciones actualizadas de planetas y Luna usando efemerides
Actualiza directamente el archivo celestial_data.json
Requiere: pip install skyfield
"""

from datetime import datetime, timezone
import sys
import os
import json


def calculate_ephemeris(location_lat=-32.4833, location_lon=-58.229561, date=None):
    """
    Calcula las coordenadas RA/DEC de planetas y Luna para una fecha y ubicacion
    
    Args:
        location_lat: Latitud del observador en grados
        location_lon: Longitud del observador en grados
        date: datetime object (si es None, usa fecha actual)
    
    Returns:
        dict: Diccionario con objetos y sus coordenadas (ra_hours, dec_degrees)
        None: Si falla (sin internet o error)
    """
    try:
        from skyfield.api import load, wgs84
    except ImportError:
        print("WARNING: skyfield no esta instalado. Usando valores predeterminados.")
        print("Instala con: pip install skyfield")
        return None
    
    try:
        print("Cargando efemerides...")
        
        # Cargar efemerides (descarga automaticamente si no existen)
        ts = load.timescale()
        eph = load('de421.bsp')
        
        # Si no se especifica fecha, usar actual
        if date is None:
            date = datetime.now(timezone.utc)
        
        # Crear tiempo Skyfield
        t = ts.from_datetime(date)
        
        # Ubicacion del observador
        observer = wgs84.latlon(location_lat, location_lon)
        
        # Objetos celestes
        earth = eph['earth']
        moon = eph['moon']
        
        planets_data = {
            'Mercurio': eph['mercury'],
            'Venus': eph['venus'],
            'Marte': eph['mars'],
            'Jupiter': eph['jupiter barycenter'],
            'Saturno': eph['saturn barycenter'],
        }
        
        results = {}
        
        print(f"\nFecha: {date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Ubicacion: {location_lat}, {location_lon}")
        print("\n" + "="*60)
        
        # Calcular Luna
        print("\nLUNA:")
        astrometric = (earth + observer).at(t).observe(moon)
        ra, dec, distance = astrometric.radec()
        ra_hours = ra.hours
        dec_degrees = dec.degrees
        results['Luna'] = (ra_hours, dec_degrees)
        print(f"  RA:  {ra_hours:.6f} horas")
        print(f"  DEC: {dec_degrees:.6f} grados")
        
        # Calcular planetas
        print("\nPLANETAS:")
        for name, body in planets_data.items():
            astrometric = (earth + observer).at(t).observe(body)
            ra, dec, distance = astrometric.radec()
            ra_hours = ra.hours
            dec_degrees = dec.degrees
            results[name] = (ra_hours, dec_degrees)
            print(f"\n  {name}:")
            print(f"    RA:  {ra_hours:.6f} horas")
            print(f"    DEC: {dec_degrees:.6f} grados")
        
        return results
    
    except Exception as e:
        print(f"ERROR al calcular efemerides: {e}")
        print("Usando valores predeterminados de celestial_data.json")
        return None


def update_json_file(ephemeris_data, filename='celestial_data.json'):
    """
    Actualiza el archivo JSON con las nuevas coordenadas
    
    Args:
        ephemeris_data: dict con coordenadas calculadas
        filename: nombre del archivo JSON
    
    Returns:
        bool: True si se actualizo correctamente
    """
    try:
        if not os.path.exists(filename):
            print(f"ERROR: Archivo '{filename}' no encontrado")
            return False
        
        # Cargar JSON existente
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Timestamp de actualizacion
        now = datetime.now(timezone.utc).isoformat()
        
        # Actualizar planetas
        for planet in data.get('planets', []):
            name = planet['name']
            if name in ephemeris_data:
                ra, dec = ephemeris_data[name]
                planet['ra_hours'] = ra
                planet['dec_degrees'] = dec
                planet['last_update'] = now
                print(f"  Actualizado: {name}")
        
        # Actualizar Luna
        if 'Luna' in ephemeris_data:
            ra, dec = ephemeris_data['Luna']
            data['moon']['ra_hours'] = ra
            data['moon']['dec_degrees'] = dec
            data['moon']['last_update'] = now
            print(f"  Actualizado: Luna")
        
        # Actualizar metadata
        if 'metadata' not in data:
            data['metadata'] = {}
        data['metadata']['last_full_update'] = now
        
        # Guardar JSON actualizado
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nArchivo '{filename}' actualizado correctamente")
        return True
    
    except Exception as e:
        print(f"\nERROR al actualizar archivo: {e}")
        return False


def print_coordinates(ephemeris_data):
    """Imprime las coordenadas calculadas en formato legible"""
    print("\n" + "="*60)
    print("COORDENADAS CALCULADAS:")
    print("="*60)
    
    for name in ['Mercurio', 'Venus', 'Marte', 'Jupiter', 'Saturno', 'Luna']:
        if name in ephemeris_data:
            ra, dec = ephemeris_data[name]
            print(f"\n{name:12s} | RA: {ra:10.6f} h | DEC: {dec:10.6f} deg")


def main():
    """Funcion principal"""
    print("="*60)
    print("CALCULADORA DE EFEMERIDES ASTRONOMICAS")
    print("="*60)
    
    # Ubicacion: Concepcion del Uruguay, Entre Rios, Argentina
    lat = -32.4833
    lon = -58.229561
    
    # Calcular efemerides
    ephemeris = calculate_ephemeris(lat, lon)
    
    if ephemeris is None:
        print("\nNo se pudieron calcular efemerides.")
        print("Verifica:")
        print("  1. Conexion a internet")
        print("  2. Instalacion de skyfield: pip install skyfield")
        sys.exit(1)
    
    # Mostrar coordenadas
    print_coordinates(ephemeris)
    
    # Preguntar si actualizar archivo
    print("\n" + "="*60)
    print("Deseas actualizar celestial_data.json? (s/n): ", end='')
    response = input().strip().lower()
    
    if response in ['s', 'si', 'y', 'yes']:
        success = update_json_file(ephemeris)
        if success:
            print("\nListo! Reinicia la aplicacion para ver los cambios.")
    else:
        print("\nNo se actualizo el archivo.")


if __name__ == "__main__":
    main()
