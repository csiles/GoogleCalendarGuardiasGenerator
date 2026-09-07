"""
Sincronizador con Google Calendar API
Soporta calendarios compartidos y sincronización bidireccional
"""

import os
import json
import logging
from datetime import datetime, timedelta
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
    CONFIG_FILE = 'json/google_config.json'
    
    def __init__(self):
        """Inicializa el sincronizador"""
        self.service = None
        self.calendar_id = None
        self.credentials = None
        self._load_config()
        
    def _load_config(self):
        """Carga configuración guardada (calendario seleccionado)"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.calendar_id = config.get('calendar_id')
                    logger.info(f"Configuración cargada: {config.get('calendar_name')}")
            except Exception as e:
                logger.warning(f"Error cargando configuración: {e}")
    
    def _save_config(self, calendar_id: str, calendar_name: str, access_role: str):
        """Guarda configuración del calendario seleccionado"""
        config = {
            'calendar_id': calendar_id,
            'calendar_name': calendar_name,
            'access_role': access_role,
            'configured_at': datetime.now().isoformat()
        }
        
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.calendar_id = calendar_id
        logger.info(f"Configuración guardada: {calendar_name}")
        
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
                os.makedirs(os.path.dirname(self.TOKEN_FILE), exist_ok=True)
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
    
    def list_available_calendars(self) -> List[Dict]:
        """
        Lista todos los calendarios accesibles (propios y compartidos).
        
        Returns:
            List[Dict]: Lista de calendarios con id, name, access_role, is_primary
        """
        try:
            if not self.service:
                raise RuntimeError("Debe autenticarse primero")
            
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            # Filtrar solo calendarios con permisos de escritura
            writable_calendars = []
            for cal in calendars:
                access_role = cal.get('accessRole', '')
                if access_role in ['owner', 'writer']:
                    writable_calendars.append({
                        'id': cal['id'],
                        'name': cal['summary'],
                        'access_role': access_role,
                        'is_primary': cal.get('primary', False),
                        'description': cal.get('description', ''),
                        'timezone': cal.get('timeZone', 'Europe/Madrid')
                    })
            
            logger.info(f"Encontrados {len(writable_calendars)} calendarios con permisos de escritura")
            return writable_calendars
            
        except HttpError as error:
            logger.error(f"Error listando calendarios: {error}")
            raise
    
    def set_calendar(self, calendar_id: str, calendar_name: str, access_role: str):
        """
        Configura el calendario a utilizar.
        
        Args:
            calendar_id: ID del calendario de Google
            calendar_name: Nombre del calendario
            access_role: Nivel de acceso (owner/writer)
        """
        self._save_config(calendar_id, calendar_name, access_role)
        logger.info(f"Calendario configurado: {calendar_name} ({access_role})")
    
    def sync_event(self, evento: dict) -> dict:
        """
        Sincroniza un evento a Google Calendar.
        
        Args:
            evento: Diccionario con:
                - titulo: str
                - descripcion: str (opcional)
                - fecha: str (YYYY-MM-DD)
                - tipo: str (opcional)
                - google_event_id: str (opcional, para updates)
                
        Returns:
            dict: Evento sincronizado con google_event_id y link
        """
        try:
            if not self.calendar_id:
                raise RuntimeError("Debe configurar un calendario primero")
            
            # Construir cuerpo del evento en formato Google Calendar
            event_body = {
                'summary': evento['titulo'],
                'description': evento.get('descripcion', ''),
                'start': {
                    'date': evento['fecha'],
                    'timeZone': 'Europe/Madrid'
                },
                'end': {
                    'date': (datetime.strptime(evento['fecha'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'timeZone': 'Europe/Madrid'
                },
                'source': {
                    'title': 'Guardias Generator',
                    'url': 'https://github.com/csiles/GoogleCalendarGuardiasGenerator'
                }
            }
            
            # Añadir color si el técnico tiene uno asignado
            if 'color' in evento and evento['color']:
                # Google Calendar tiene colores predefinidos (1-11)
                # Mapear colores hex a IDs de Google
                color_id = self._map_color_to_google(evento['color'])
                if color_id:
                    event_body['colorId'] = color_id
            
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
                # Buscar si ya existe en Google para evitar duplicados
                existing_id = self._find_existing_event(evento['fecha'], evento['titulo'])
                if existing_id:
                    result = self.service.events().update(
                        calendarId=self.calendar_id,
                        eventId=existing_id,
                        body=event_body
                    ).execute()
                    logger.debug(f"Evento existente encontrado y actualizado: {evento['titulo']}")
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
    
    def _map_color_to_google(self, hex_color: str) -> Optional[str]:
        """
        Mapea colores hex a IDs de colores de Google Calendar.
        
        Args:
            hex_color: Color en formato #RRGGBB
            
        Returns:
            str: ID de color de Google (1-11) o None
        """
        # Mapeo aproximado de colores
        color_mapping = {
            '#3498db': '9',   # Azul -> Blue
            '#e74c3c': '11',  # Rojo -> Red
            '#2ecc71': '10',  # Verde -> Green
            '#f39c12': '6',   # Naranja -> Orange
            '#9b59b6': '3',   # Morado -> Purple
            '#1abc9c': '7',   # Turquesa -> Cyan
        }
        return color_mapping.get(hex_color.lower())
    
    def _find_existing_event(self, fecha: str, titulo: str) -> Optional[str]:
        """
        Busca en Google Calendar si ya existe un evento con ese título en esa fecha.
        Evita duplicados cuando el evento fue creado manualmente en Google.

        Args:
            fecha: Fecha en formato YYYY-MM-DD
            titulo: Título del evento a buscar

        Returns:
            str: ID del evento existente, o None si no existe
        """
        try:
            time_min = f"{fecha}T00:00:00Z"
            # Para eventos de todo el día, buscar hasta el día siguiente
            from datetime import datetime as _dt
            next_day = (_dt.strptime(fecha, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            time_max = f"{next_day}T00:00:00Z"

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True
            ).execute()

            for event in events_result.get('items', []):
                if event.get('summary', '').lower() == titulo.lower():
                    return event['id']
            return None
        except Exception as e:
            logger.warning(f"Error buscando evento existente: {e}")
            return None

    def sync_bulk(self, eventos: List[dict], progress_callback=None) -> dict:
        """
        Sincroniza múltiples eventos en batch.
        
        Args:
            eventos: Lista de eventos a sincronizar
            progress_callback: Función(current, total, evento_nombre) para progreso
            
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
                was_update = bool(evento.get('google_event_id'))
                result = self.sync_event(evento)
                
                # Actualizar evento con google_event_id
                evento['google_event_id'] = result['google_event_id']
                evento['google_link'] = result['link']
                
                if was_update:
                    stats['updated'] += 1
                else:
                    stats['created'] += 1
                
                # Callback de progreso
                if progress_callback:
                    progress_callback(i + 1, len(eventos), evento.get('titulo', ''))
                    
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
    
    def pull_events(self, time_min: datetime, time_max: datetime) -> List[dict]:
        """
        Descarga eventos desde Google Calendar en un rango de fechas.
        
        Args:
            time_min: Fecha inicial
            time_max: Fecha final
            
        Returns:
            list: Eventos modificados en Google Calendar
        """
        try:
            if not self.calendar_id:
                raise RuntimeError("Debe configurar un calendario primero")
            
            # Formatear fechas en RFC3339
            time_min_str = time_min.strftime('%Y-%m-%dT00:00:00Z')
            time_max_str = time_max.strftime('%Y-%m-%dT23:59:59Z')
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            logger.info(f"Descargados {len(events)} eventos desde Google Calendar")
            
            # Convertir a formato interno
            converted_events = []
            for event in events:
                # Obtener fecha del evento
                start = event['start'].get('date')
                if not start:
                    # Si es un evento con hora, obtener solo la fecha
                    start = event['start'].get('dateTime', '')[:10]
                
                converted = {
                    'google_event_id': event['id'],
                    'titulo': event.get('summary', 'Sin título'),
                    'descripcion': event.get('description', ''),
                    'fecha': start,
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
            if not self.calendar_id:
                raise RuntimeError("Debe configurar un calendario primero")
            
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=google_event_id
            ).execute()
            
            logger.info(f"Evento eliminado de Google: {google_event_id}")
            
        except HttpError as error:
            if error.resp.status == 404:
                logger.warning(f"Evento no encontrado en Google: {google_event_id}")
            else:
                logger.error(f"Error eliminando evento: {error}")
                raise
    
    def get_calendar_url(self) -> str:
        """Obtiene URL pública del calendario"""
        if self.calendar_id:
            return f"https://calendar.google.com/calendar/embed?src={self.calendar_id}"
        return None
    
    def is_configured(self) -> bool:
        """Verifica si hay un calendario configurado"""
        return self.calendar_id is not None
    
    def get_config(self) -> Optional[Dict]:
        """Obtiene la configuración actual"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None
