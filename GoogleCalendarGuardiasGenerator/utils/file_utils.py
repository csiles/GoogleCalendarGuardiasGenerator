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
        list: Lista de nombres de técnicos
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tecnicos = [line.strip() for line in f if line.strip()]
        return tecnicos
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error cargando técnicos: {e}")
        return []


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
    Retorna mapeo de colores para técnicos.
    
    Returns:
        dict: Diccionario de colores por técnico
    """
    return {
        'Pilar': '#FF6B6B',    # Rojo coral
        'Isa': '#4ECDC4',      # Turquesa
        'Romane': '#95E1D3',   # Verde menta
        'Yannick': '#FFD93D',  # Amarillo
        'Mayra': '#C77DFF',    # Morado
        'Alberto': '#6BCB77'   # Verde
    }
