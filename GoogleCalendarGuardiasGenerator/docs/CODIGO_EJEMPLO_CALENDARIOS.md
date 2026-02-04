# 💻 Código de Ejemplo: Gestor de Calendarios + Google Sync

Este documento contiene código listo para implementar basado en el análisis técnico.

---

## 📦 Instalación de Dependencias

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Dependencias para gestor de calendarios
pip install pandas

# Dependencias para Google Calendar
pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

## 📄 Ejemplo 1: CalendarManager (calendar_manager.py)

```python
"""
Gestor de calendarios históricos y futuros con persistencia JSON
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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
                    return json.load(f)
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
        Importa eventos desde archivo CSV.
        
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
            # Leer CSV
            df = pd.read_csv(filepath, encoding='utf-8')
            
            # Validar columnas requeridas
            required_cols = ['fecha', 'tipo', 'titulo']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Columnas faltantes: {', '.join(missing_cols)}")
            
            stats['total'] = len(df)
            
            # Calcular hash del archivo para detección de duplicados
            file_hash = self._calculate_file_hash(filepath)
            
            # Verificar si ya fue importado
            if self._is_csv_imported(file_hash):
                logger.warning(f"CSV ya importado previamente: {filepath}")
                stats['duplicados'] = len(df)
                return stats
            
            # Procesar cada fila
            for idx, row in df.iterrows():
                try:
                    # Validar fecha
                    fecha = pd.to_datetime(row['fecha']).strftime('%Y-%m-%d')
                    
                    # Crear evento
                    evento = {
                        'id': self._generate_event_id(fecha, row['titulo']),
                        'titulo': str(row['titulo']),
                        'tipo': str(row['tipo']),
                        'descripcion': str(row.get('descripcion', '')),
                        'categoria': str(row.get('categoria', '')),
                        'origen': 'csv_import',
                        'fecha_importacion': datetime.now().isoformat(),
                        'archivo_origen': os.path.basename(filepath)
                    }
                    
                    # Agregar evento
                    if self.add_event(fecha, evento):
                        stats['importados'] += 1
                    else:
                        stats['duplicados'] += 1
                        
                except Exception as e:
                    stats['errores'] += 1
                    stats['errores_detalle'].append({
                        'fila': idx + 2,  # +2 porque idx empieza en 0 y header es fila 1
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
        
    def export_to_csv(self, output_path: str, start_date: str = None, 
                      end_date: str = None) -> str:
        """
        Exporta eventos a CSV.
        
        Args:
            output_path: Ruta de salida
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)
            
        Returns:
            str: Ruta del archivo creado
        """
        eventos = self.get_all_events()
        
        # Filtrar por fechas si se especifican
        if start_date:
            eventos = [e for e in eventos if e['fecha'] >= start_date]
        if end_date:
            eventos = [e for e in eventos if e['fecha'] <= end_date]
            
        # Crear DataFrame
        df = pd.DataFrame(eventos)
        
        # Reordenar columnas
        cols_order = ['fecha', 'tipo', 'titulo', 'descripcion', 'categoria']
        cols_order = [c for c in cols_order if c in df.columns]
        df = df[cols_order]
        
        # Guardar CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Exportados {len(eventos)} eventos a {output_path}")
        return output_path
        
    def get_statistics(self) -> dict:
        """Obtiene estadísticas globales"""
        total_meses = len(self.data['meses'])
        total_eventos = sum(
            m['estadisticas_mes']['total_eventos'] 
            for m in self.data['meses'].values()
        )
        
        # Eventos por tipo
        eventos_por_tipo = {}
        for month_data in self.data['meses'].values():
            for tipo, count in month_data['estadisticas_mes'].get('por_tipo', {}).items():
                eventos_por_tipo[tipo] = eventos_por_tipo.get(tipo, 0) + count
                
        return {
            'total_meses_con_datos': total_meses,
            'total_eventos': total_eventos,
            'eventos_por_tipo': eventos_por_tipo,
            'fuentes_csv': len(self.data['fuentes_csv']),
            'ultima_actualizacion': self.data['last_updated']
        }
```

---

## 📄 Ejemplo 2: GoogleCalendarSync (google_calendar_sync.py)

```python
"""
Sincronizador con Google Calendar API
Requiere configuración previa en Google Cloud Console
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleCalendarSync:
    """Sincronizador bidireccional con Google Calendar"""
    
    # Scope para acceso completo a calendarios
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    # Archivos de configuración
    TOKEN_FILE = 'json/google_token.json'
    CREDENTIALS_FILE = 'json/google_credentials.json'
    
    # Colores para tipos de eventos
    COLOR_MAP = {
        'festivo': '11',        # Rojo
        'deadline': '6',        # Naranja
        'evento': '9',          # Azul
        'mantenimiento': '8',   # Gris
        'default': '1'          # Lavanda
    }
    
    def __init__(self):
        """Inicializa el sincronizador"""
        self.service = None
        self.calendar_id = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """
        Realiza autenticación OAuth 2.0.
        
        Returns:
            bool: True si autenticación exitosa
        """
        try:
            creds = None
            
            # El token ya existe
            if os.path.exists(self.TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(
                    self.TOKEN_FILE, self.SCOPES
                )
            
            # Token expirado o no existe
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refrescar token expirado
                    logger.info("Refrescando token de Google...")
                    creds.refresh(Request())
                else:
                    # Nuevo flujo de autenticación
                    if not os.path.exists(self.CREDENTIALS_FILE):
                        raise FileNotFoundError(
                            f"Archivo de credenciales no encontrado: {self.CREDENTIALS_FILE}\n"
                            "Descárgalo desde Google Cloud Console"
                        )
                    
                    logger.info("Iniciando flujo de autenticación OAuth 2.0...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CREDENTIALS_FILE, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Guardar token para futuros usos
                with open(self.TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"Token guardado en {self.TOKEN_FILE}")
            
            # Crear servicio de Calendar API
            self.service = build('calendar', 'v3', credentials=creds)
            self.credentials = creds
            
            logger.info("✅ Autenticación exitosa con Google Calendar")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en autenticación: {e}")
            raise
            
    def create_or_get_calendar(self, name: str = "Freshdesk Reports") -> str:
        """
        Crea o obtiene calendario dedicado.
        
        Args:
            name: Nombre del calendario
            
        Returns:
            str: ID del calendario
        """
        try:
            # Listar calendarios existentes
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            # Buscar calendario existente
            for cal in calendars:
                if cal['summary'] == name:
                    logger.info(f"Calendario existente encontrado: {name} (ID: {cal['id']})")
                    self.calendar_id = cal['id']
                    return cal['id']
            
            # Crear nuevo calendario
            calendar = {
                'summary': name,
                'description': 'Calendario generado automáticamente desde Freshdesk Reports Creator',
                'timeZone': 'Europe/Madrid'
            }
            
            created_calendar = self.service.calendars().insert(body=calendar).execute()
            self.calendar_id = created_calendar['id']
            
            logger.info(f"✅ Calendario creado: {name} (ID: {self.calendar_id})")
            return self.calendar_id
            
        except HttpError as error:
            logger.error(f"❌ Error creando calendario: {error}")
            raise
            
    def sync_event(self, evento: dict) -> dict:
        """
        Sincroniza un evento a Google Calendar.
        
        Args:
            evento: Diccionario con:
                - titulo: str
                - descripcion: str
                - fecha: str (YYYY-MM-DD)
                - tipo: str
                - google_event_id: str (opcional, para updates)
                
        Returns:
            dict: Evento sincronizado con google_event_id y link
        """
        try:
            # Construir cuerpo del evento en formato Google Calendar
            event_body = {
                'summary': evento['titulo'],
                'description': evento.get('descripcion', ''),
                'start': {
                    'date': evento['fecha'],
                },
                'end': {
                    'date': evento['fecha'],
                },
                'colorId': self.COLOR_MAP.get(
                    evento.get('tipo', ''), 
                    self.COLOR_MAP['default']
                ),
                'source': {
                    'title': 'Freshdesk Reports Creator',
                    'url': 'https://freshdesk.com'
                }
            }
            
            # Update vs Create
            if evento.get('google_event_id'):
                # Actualizar evento existente
                result = self.service.events().update(
                    calendarId=self.calendar_id,
                    eventId=evento['google_event_id'],
                    body=event_body
                ).execute()
                
                logger.debug(f"Evento actualizado: {evento['titulo']}")
            else:
                # Crear nuevo evento
                result = self.service.events().insert(
                    calendarId=self.calendar_id,
                    body=event_body
                ).execute()
                
                logger.debug(f"Evento creado: {evento['titulo']}")
            
            return {
                'google_event_id': result['id'],
                'link': result.get('htmlLink'),
                'updated': result.get('updated')
            }
            
        except HttpError as error:
            logger.error(f"Error sincronizando evento '{evento.get('titulo')}': {error}")
            raise
            
    def sync_bulk(self, eventos: List[dict], 
                   progress_callback=None) -> dict:
        """
        Sincroniza múltiples eventos en batch.
        
        Args:
            eventos: Lista de eventos a sincronizar
            progress_callback: Función(current, total) para progreso
            
        Returns:
            dict: Estadísticas de sincronización
        """
        stats = {
            'total': len(eventos),
            'created': 0,
            'updated': 0,
            'errors': 0,
            'errores_detalle': []
        }
        
        for i, evento in enumerate(eventos):
            try:
                result = self.sync_event(evento)
                
                # Actualizar evento con google_event_id
                evento['google_event_id'] = result['google_event_id']
                
                if 'google_event_id' in evento and evento['google_event_id']:
                    stats['updated'] += 1
                else:
                    stats['created'] += 1
                
                # Callback de progreso
                if progress_callback:
                    progress_callback(i + 1, len(eventos))
                    
            except Exception as e:
                stats['errors'] += 1
                stats['errores_detalle'].append({
                    'evento': evento.get('titulo', 'Sin título'),
                    'fecha': evento.get('fecha'),
                    'error': str(e)
                })
                
        logger.info(
            f"Sincronización completada: "
            f"{stats['created']} creados, "
            f"{stats['updated']} actualizados, "
            f"{stats['errors']} errores"
        )
        
        return stats
        
    def pull_updates(self, since: datetime) -> List[dict]:
        """
        Descarga cambios desde Google Calendar.
        
        Args:
            since: Fecha desde la cual buscar cambios
            
        Returns:
            list: Eventos modificados en Google Calendar
        """
        try:
            # Formatear fecha en RFC3339
            time_min = since.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            logger.info(f"Descargados {len(events)} eventos desde {since}")
            
            # Convertir a formato interno
            converted_events = []
            for event in events:
                converted = {
                    'google_event_id': event['id'],
                    'titulo': event.get('summary', 'Sin título'),
                    'descripcion': event.get('description', ''),
                    'fecha': event['start'].get('date', event['start'].get('dateTime')[:10]),
                    'link': event.get('htmlLink'),
                    'updated': event.get('updated')
                }
                converted_events.append(converted)
                
            return converted_events
            
        except HttpError as error:
            logger.error(f"Error descargando eventos: {error}")
            raise
            
    def delete_event(self, google_event_id: str):
        """
        Elimina evento de Google Calendar.
        
        Args:
            google_event_id: ID del evento en Google
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=google_event_id
            ).execute()
            
            logger.info(f"Evento eliminado: {google_event_id}")
            
        except HttpError as error:
            logger.error(f"Error eliminando evento: {error}")
            raise
            
    def get_calendar_url(self) -> str:
        """Obtiene URL pública del calendario"""
        if self.calendar_id:
            return f"https://calendar.google.com/calendar/embed?src={self.calendar_id}"
        return None
```

---

## 📄 Ejemplo 3: CSV Template

Guardar como `plantilla_calendario.csv`:

```csv
fecha,tipo,titulo,descripcion,categoria
2026-01-01,festivo,Año Nuevo,Festivo nacional,festivo_nacional
2026-01-06,festivo,Reyes,Festivo nacional,festivo_nacional
2026-02-14,evento,San Valentín,Promoción especial,marketing
2026-03-15,deadline,Cierre Q1,Entrega de reportes trimestrales,negocio
2026-04-01,mantenimiento,Actualización servidores,Ventana de mantenimiento programada,operacional
2026-04-18,festivo,Viernes Santo,Festivo nacional,festivo_nacional
2026-05-01,festivo,Día del Trabajo,Festivo nacional,festivo_nacional
2026-12-25,festivo,Navidad,Festivo nacional,festivo_nacional
```

---

## 📄 Ejemplo 4: Setup de Google Cloud

### Paso 1: Crear proyecto en Google Cloud Console

1. Ir a: https://console.cloud.google.com
2. Click en "Select a project" → "New Project"
3. Nombre: `FreshdeskReportsCalendar`
4. Click "Create"

### Paso 2: Habilitar Google Calendar API

1. En el menú, ir a "APIs & Services" → "Library"
2. Buscar "Google Calendar API"
3. Click "Enable"

### Paso 3: Crear credenciales OAuth 2.0

1. Ir a "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Si es primera vez, configurar "OAuth consent screen":
   - User Type: External
   - App name: Freshdesk Reports Creator
   - User support email: tu-email@empresa.com
   - Developer contact: tu-email@empresa.com
4. Application type: "Desktop app"
5. Name: "Freshdesk Reports Desktop"
6. Click "Create"
7. **Descargar JSON** → guardar como `json/google_credentials.json`

### Paso 4: Actualizar .gitignore

```gitignore
# Google Calendar credentials (IMPORTANTE!)
json/google_token.json
json/google_credentials.json
```

---

## 📄 Ejemplo 5: Script de Testing

```python
"""
Script para probar funcionalidades del gestor de calendarios
"""

from calendar_manager import CalendarManager
from google_calendar_sync import GoogleCalendarSync
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_calendar_manager():
    """Test básico del CalendarManager"""
    print("\n=== TEST CALENDAR MANAGER ===")
    
    # Crear manager
    cm = CalendarManager()
    
    # Añadir evento manualmente
    evento = {
        'id': 'test_001',
        'titulo': 'Evento de Prueba',
        'tipo': 'evento',
        'descripcion': 'Testing del sistema'
    }
    
    cm.add_event('2026-02-15', evento)
    print("✅ Evento añadido")
    
    # Obtener vista del mes
    vista = cm.get_month_view(2026, 2)
    print(f"✅ Vista de mes obtenida: {vista['estadisticas_mes']}")
    
    # Guardar
    cm.save_data()
    print("✅ Datos guardados")
    
    # Estadísticas
    stats = cm.get_statistics()
    print(f"📊 Estadísticas: {stats}")

def test_csv_import():
    """Test de importación CSV"""
    print("\n=== TEST CSV IMPORT ===")
    
    cm = CalendarManager()
    
    # Importar CSV (asume que existe plantilla_calendario.csv)
    stats = cm.import_csv('plantilla_calendario.csv')
    
    print(f"📊 Importación:")
    print(f"  Total: {stats['total']}")
    print(f"  Importados: {stats['importados']}")
    print(f"  Duplicados: {stats['duplicados']}")
    print(f"  Errores: {stats['errores']}")

def test_google_sync():
    """Test de Google Calendar Sync (requiere credenciales)"""
    print("\n=== TEST GOOGLE SYNC ===")
    
    try:
        # Autenticar
        sync = GoogleCalendarSync()
        sync.authenticate()
        print("✅ Autenticación exitosa")
        
        # Crear/obtener calendario
        cal_id = sync.create_or_get_calendar("Test Calendar")
        print(f"✅ Calendario: {cal_id}")
        
        # Sincronizar evento de prueba
        evento = {
            'titulo': 'Test Sync Event',
            'descripcion': 'Evento de prueba de sincronización',
            'fecha': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'tipo': 'evento'
        }
        
        result = sync.sync_event(evento)
        print(f"✅ Evento sincronizado: {result['link']}")
        
    except FileNotFoundError as e:
        print(f"⚠️ Credenciales no configuradas: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_calendar_manager()
    # test_csv_import()  # Descomentar si existe CSV
    # test_google_sync()  # Descomentar si credenciales configuradas
```

---

## 🎯 Quick Start Guide

### 1. Instalar dependencias
```bash
pip install pandas google-auth google-auth-oauthlib google-api-python-client
```

### 2. Copiar archivos
- `calendar_manager.py` → raíz del proyecto
- `google_calendar_sync.py` → raíz del proyecto

### 3. Configurar Google (opcional)
- Seguir pasos de "Setup de Google Cloud"
- Descargar `credentials.json` → `json/google_credentials.json`

### 4. Probar funcionalidades
```bash
python test_calendarios.py
```

---

**Última actualización:** 2 de febrero de 2026  
**Estado:** ✅ Ready to Use
