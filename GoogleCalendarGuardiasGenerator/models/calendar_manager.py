"""
Gestor de calendarios históricos y futuros con persistencia JSON
"""

import json
import os
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class CalendarManager:
    """Gestor de calendarios con soporte para importación CSV"""
    
    def __init__(self, data_file: str = "json/calendarios.json"):
        """
        Inicializa el gestor de calendarios.
        
        Args:
            data_file: Ruta al archivo JSON de persistencia
        """
        self.data_file = data_file
        self.data = self._load_data()
        
    def _load_data(self) -> dict:
        """Carga datos desde JSON o crea estructura inicial"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Validar que tenga las claves necesarias
                if 'meses' not in data or 'fuentes_csv' not in data:
                    logger.warning(f"Estructura de datos incompleta en {self.data_file}, regenerando...")
                    return self._get_empty_structure()
                
                return data
            except Exception as e:
                logger.error(f"Error cargando {self.data_file}: {e}")
                return self._get_empty_structure()
        else:
            return self._get_empty_structure()
            
    def _get_empty_structure(self) -> dict:
        """Retorna estructura vacía de datos"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "meses": {},
            "fuentes_csv": []
        }
        
    def save_data(self):
        """Persiste datos a JSON"""
        self.data["last_updated"] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Datos guardados en {self.data_file}")
        
    def import_csv(self, filepath: str) -> dict:
        """
        Importa eventos desde archivo CSV generado por la aplicación.
        
        Args:
            filepath: Ruta al archivo CSV
            
        Returns:
            dict: Estadísticas de importación
        """
        stats = {
            'total': 0,
            'importados': 0,
            'duplicados': 0,
            'errores': 0,
            'errores_detalle': []
        }
        
        try:
            # Calcular hash del archivo para detección de duplicados
            file_hash = self._calculate_file_hash(filepath)
            
            # Verificar si ya fue importado
            if self._is_csv_imported(file_hash):
                logger.warning(f"CSV ya importado previamente: {filepath}")
                return stats
            
            # Leer CSV
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            stats['total'] = len(rows)
            
            # Procesar cada fila
            for idx, row in enumerate(rows):
                try:
                    # Parsear fechas en formato YYYY-MM-DD
                    fecha_inicio_str = row['Start Date']
                    fecha_fin_str = row['End Date']
                    
                    fecha_inicio_obj = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
                    fecha_fin_obj = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
                    
                    # Extraer nombre del técnico del Subject (formato: "Guardia - Nombre" o "Guardia TARDE - Nombre")
                    subject = str(row['Subject'])
                    tecnico = subject.split(' - ')[-1].strip() if ' - ' in subject else subject
                    
                    # Para eventos All Day, el End Date es exclusivo (hasta el inicio de ese día, no lo incluye)
                    is_all_day = row.get('All Day Event', 'True') == 'True'
                    
                    # Crear evento para cada día en el rango
                    fecha_actual = fecha_inicio_obj
                    # Para All Day events, End Date es exclusivo (no se incluye)
                    fecha_limite = fecha_fin_obj if not is_all_day else fecha_fin_obj - timedelta(days=1)
                    
                    while fecha_actual <= fecha_limite:
                        fecha = fecha_actual.strftime('%Y-%m-%d')
                        
                        # Verificar si ya existe un evento en esta fecha
                        year_month = fecha[:7]
                        day = fecha[8:10]
                        existing_tecnico = None
                        
                        if year_month in self.data['meses']:
                            if day in self.data['meses'][year_month]['dias']:
                                eventos_dia = self.data['meses'][year_month]['dias'][day]['eventos']
                                if eventos_dia:
                                    existing_tecnico = eventos_dia[0].get('tecnico')
                        
                        # Solo añadir si no hay evento previo en esta fecha
                        if not existing_tecnico:
                            evento = {
                                'id': self._generate_event_id(fecha, subject),
                                'titulo': subject,
                                'tecnico': tecnico,
                                'tipo': 'guardia',
                                'descripcion': str(row.get('Description', '')),
                                'all_day': is_all_day,
                                'origen': 'csv_import',
                                'fecha_importacion': datetime.now().isoformat(),
                                'archivo_origen': os.path.basename(filepath)
                            }
                            
                            # Agregar evento
                            if self.add_event(fecha, evento):
                                stats['importados'] += 1
                            else:
                                stats['duplicados'] += 1
                        else:
                            logger.warning(f"Conflicto en {fecha}: ya existe guardia de {existing_tecnico}, ignorando {tecnico}")
                            stats['duplicados'] += 1
                        
                        # Siguiente día
                        fecha_actual += timedelta(days=1)
                        
                except Exception as e:
                    stats['errores'] += 1
                    stats['errores_detalle'].append({
                        'fila': idx + 2,
                        'error': str(e)
                    })
                    
            # Registrar fuente CSV
            self.data['fuentes_csv'].append({
                'nombre': os.path.basename(filepath),
                'ruta': filepath,
                'fecha_carga': datetime.now().isoformat(),
                'registros_importados': stats['importados'],
                'hash': file_hash
            })
            
            # Guardar cambios
            self.save_data()
            
            logger.info(f"CSV importado: {stats['importados']} eventos de {stats['total']} total")
            
        except Exception as e:
            logger.error(f"Error importando CSV {filepath}: {e}")
            stats['errores'] += 1
            stats['errores_detalle'].append({'error': str(e)})
            
        return stats
        
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calcula hash MD5 del archivo"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def _is_csv_imported(self, file_hash: str) -> bool:
        """Verifica si un CSV ya fue importado"""
        for fuente in self.data['fuentes_csv']:
            if fuente.get('hash') == file_hash:
                return True
        return False
        
    def _generate_event_id(self, fecha: str, titulo: str) -> str:
        """Genera ID único para evento"""
        base = f"{fecha}_{titulo}"
        return hashlib.md5(base.encode()).hexdigest()[:16]
        
    def add_event(self, fecha: str, evento: dict) -> bool:
        """
        Añade evento a una fecha específica.
        
        Args:
            fecha: Fecha en formato YYYY-MM-DD
            evento: Diccionario con datos del evento
            
        Returns:
            bool: True si se añadió, False si ya existía
        """
        # Extraer año-mes
        year_month = fecha[:7]  # "2026-02"
        
        # Crear estructura si no existe
        if year_month not in self.data['meses']:
            self.data['meses'][year_month] = {
                'dias': {},
                'estadisticas_mes': {
                    'total_eventos': 0,
                    'por_tipo': {}
                }
            }
            
        month_data = self.data['meses'][year_month]
        
        # Crear día si no existe
        day = fecha[8:10]  # "15"
        if day not in month_data['dias']:
            month_data['dias'][day] = {
                'eventos': [],
                'metricas': {}
            }
            
        # Verificar duplicados
        event_id = evento.get('id')
        existing_ids = [e.get('id') for e in month_data['dias'][day]['eventos']]
        
        if event_id in existing_ids:
            logger.debug(f"Evento duplicado evitado: {evento.get('titulo')}")
            return False
            
        # Agregar evento
        month_data['dias'][day]['eventos'].append(evento)
        
        # Actualizar estadísticas
        month_data['estadisticas_mes']['total_eventos'] += 1
        tipo = evento.get('tipo', 'otro')
        month_data['estadisticas_mes']['por_tipo'][tipo] = \
            month_data['estadisticas_mes']['por_tipo'].get(tipo, 0) + 1
            
        return True
        
    def get_month_view(self, year: int, month: int) -> dict:
        """
        Obtiene vista completa de un mes.
        
        Args:
            year: Año
            month: Mes (1-12)
            
        Returns:
            dict: Datos del mes
        """
        year_month = f"{year:04d}-{month:02d}"
        return self.data['meses'].get(year_month, {
            'dias': {},
            'estadisticas_mes': {'total_eventos': 0}
        })
        
    def get_multi_month_view(self, start_date: datetime, months: int) -> List[dict]:
        """
        Obtiene vista de múltiples meses consecutivos.
        
        Args:
            start_date: Fecha de inicio
            months: Número de meses a incluir
            
        Returns:
            list: Lista de diccionarios con datos de cada mes
        """
        views = []
        current = start_date
        
        for i in range(months):
            month_data = self.get_month_view(current.year, current.month)
            month_data['year'] = current.year
            month_data['month'] = current.month
            month_data['month_name'] = current.strftime('%B %Y')
            views.append(month_data)
            
            # Siguiente mes
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
                
        return views
        
    def get_all_events(self) -> List[dict]:
        """
        Obtiene todos los eventos de todos los meses.
        
        Returns:
            list: Lista de todos los eventos con fecha
        """
        all_events = []
        
        for year_month, month_data in self.data['meses'].items():
            for day, day_data in month_data['dias'].items():
                for evento in day_data['eventos']:
                    event_copy = evento.copy()
                    event_copy['fecha'] = f"{year_month}-{day}"
                    all_events.append(event_copy)
                    
        return all_events
        
    def get_statistics(self) -> dict:
        """Obtiene estadísticas globales"""
        # Asegurar que la estructura existe
        if 'meses' not in self.data:
            self.data['meses'] = {}
        if 'fuentes_csv' not in self.data:
            self.data['fuentes_csv'] = []
        
        total_meses = len(self.data.get('meses', {}))
        total_eventos = sum(
            m.get('estadisticas_mes', {}).get('total_eventos', 0)
            for m in self.data.get('meses', {}).values()
        )
        
        # Eventos por tipo
        eventos_por_tipo = {}
        for month_data in self.data.get('meses', {}).values():
            for tipo, count in month_data.get('estadisticas_mes', {}).get('por_tipo', {}).items():
                eventos_por_tipo[tipo] = eventos_por_tipo.get(tipo, 0) + count
                
        return {
            'total_meses_con_datos': total_meses,
            'total_eventos': total_eventos,
            'eventos_por_tipo': eventos_por_tipo,
            'fuentes_csv': len(self.data.get('fuentes_csv', [])),
            'ultima_actualizacion': self.data.get('last_updated', datetime.now().isoformat())
        }
