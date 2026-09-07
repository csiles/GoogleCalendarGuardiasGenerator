"""
Utilidades para lectura de archivos de configuración
"""

from typing import List, Dict
from datetime import datetime


def load_tecnicos(filepath: str = "tecnicos.txt") -> List[str]:
    """
    Carga lista de técnicos desde archivo.
    
    Args:
        filepath: Ruta al archivo de técnicos
        
    Returns:
        list: Lista de nombres de técnicos (sin colores)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tecnicos = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Formato: Nombre,#color
                nombre = line.split(',')[0].strip()
                tecnicos.append(nombre)
        return tecnicos
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error cargando técnicos: {e}")
        return []


def load_tecnicos_with_colors(filepath: str = "tecnicos.txt") -> Dict[str, str]:
    """
    Carga técnicos con sus colores desde archivo.
    
    Args:
        filepath: Ruta al archivo de técnicos
        
    Returns:
        dict: Diccionario {nombre: color}
    """
    tecnicos_colors = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Formato: Nombre,#color
                parts = line.split(',')
                if len(parts) >= 2:
                    nombre = parts[0].strip()
                    color = parts[1].strip()
                    tecnicos_colors[nombre] = color
                else:
                    # Fallback si no tiene color definido
                    nombre = parts[0].strip()
                    tecnicos_colors[nombre] = '#3498db'  # Color por defecto
        return tecnicos_colors
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error cargando técnicos con colores: {e}")
        return {}


def load_festivos(filepath: str = "festivos.txt") -> Dict[datetime, str]:
    """
    Carga festivos desde archivo.
    
    Args:
        filepath: Ruta al archivo de festivos
        
    Returns:
        dict: Diccionario {fecha: descripción}
    """
    festivos = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                # Formato: DD/MM/YYYY o DD/MM/YYYY,DESCRIPCION
                parts = line.split(',')
                fecha_str = parts[0].strip()
                descripcion = parts[1].strip() if len(parts) > 1 else ""
                
                try:
                    fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                    festivos[fecha] = descripcion
                except ValueError:
                    print(f"Fecha inválida ignorada: {fecha_str}")
                    
        return festivos
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error cargando festivos: {e}")
        return {}


def get_technician_colors() -> Dict[str, str]:
    """
    Retorna mapeo de colores para técnicos desde el archivo tecnicos.txt.
    
    Returns:
        dict: Diccionario de colores por técnico
    """
    return load_tecnicos_with_colors()
