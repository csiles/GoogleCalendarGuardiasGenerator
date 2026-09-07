# 📊 Análisis Técnico: Gestor de Calendarios y Google Calendar Integration

**Fecha:** 2 de febrero de 2026  
**Rol:** CTO & Senior Integration Architect  
**Proyecto:** Freshdesk Reports Creator - Calendar Manager Module

---

## 🎯 Executive Summary

Se analizan dos funcionalidades complementarias:
1. **Gestor de Calendarios Históricos y Futuros** - Sistema de visualización y gestión de calendarios
2. **Integración con Google Calendar** - Sincronización automática de calendarios generados

**Recomendación:** ✅ Ambas funcionalidades son técnicamente viables con ROI positivo

---

## 📋 PARTE 1: GESTOR DE CALENDARIOS

### 1.1 Análisis de Requisitos

#### Requisitos Funcionales
- ✅ Vista histórica: 3 meses atrás (expandible a más)
- ✅ Vista futura: mes actual + 3 meses adelante
- ✅ Importación de CSV desde Google Drive/local
- ✅ Persistencia de datos históricos
- ✅ Interfaz integrada (pestaña nueva vs modal)

#### Requisitos No Funcionales
- **Performance:** Renderizado de 7 meses simultáneos (< 1 seg)
- **Usabilidad:** Navegación intuitiva entre períodos
- **Escalabilidad:** Soporte para años de histórico sin degradación
- **Persistencia:** JSON local con backup automático

---

### 1.2 Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                    TabCalendario (Nueva Pestaña)            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────────────┐ │
│  │  Control Panel  │  │    Timeline Visualization        │ │
│  ├─────────────────┤  ├──────────────────────────────────┤ │
│  │ • Cargar CSV    │  │ ◄◄  -3  -2  -1  HOY  +1  +2  +3 ►►│ │
│  │ • Exportar      │  │                                  │ │
│  │ • Filtros       │  │  [Calendar Grid - 7 meses]       │ │
│  │ • Navegación    │  │                                  │ │
│  └─────────────────┘  └──────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Detalles del Período Seleccionado            │  │
│  │  • Estadísticas • Eventos • Tickets • Tendencias     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### 1.3 Stack Tecnológico Recomendado

#### Opción A: Nativa con Tkinter (Recomendada)
```python
# Bibliotecas necesarias
- tkcalendar.Calendar      # Ya instalada, vista mensual
- tkinter.Canvas           # Grid personalizado de múltiples meses
- pandas                   # Procesamiento CSV
- json                     # Persistencia local
```

**Pros:**
- ✅ Sin dependencias externas complejas
- ✅ Consistencia con UI actual
- ✅ Control total del rendering
- ✅ Offline-first

**Contras:**
- ⚠️ Desarrollo custom para multi-month view
- ⚠️ Limitaciones visuales de Tkinter

#### Opción B: WebView Embebido
```python
# Stack alternativo
- webview                  # Browser embebido
- fullcalendar.js         # Librería JavaScript de calendarios
- Flask (mini-server)     # Backend local
```

**Pros:**
- ✅ UI moderna y rica
- ✅ Interactividad superior
- ✅ Drag & drop nativo

**Contras:**
- ❌ Mayor complejidad arquitectural
- ❌ Dependencia de recursos web
- ❌ Mayor footprint de memoria

**DECISIÓN:** Opción A para MVP, considerar B para v2.0

---

### 1.4 Modelo de Datos

```json
{
  "calendarios": {
    "version": "1.0",
    "last_updated": "2026-02-02T10:30:00Z",
    "meses": {
      "2025-11": {
        "dias": {
          "01": {
            "eventos": [
              {
                "id": "evt_001",
                "tipo": "festivo",
                "titulo": "Todos los Santos",
                "descripcion": "Festivo nacional",
                "tickets_afectados": [],
                "origen": "csv_import",
                "fecha_importacion": "2026-02-01"
              }
            ],
            "metricas": {
              "tickets_creados": 45,
              "tickets_cerrados": 38,
              "carga_trabajo": "media"
            }
          }
        },
        "estadisticas_mes": {
          "total_eventos": 12,
          "dias_laborables": 22,
          "festivos": 1,
          "picos_carga": ["15", "22"]
        }
      }
    },
    "fuentes_csv": [
      {
        "nombre": "calendario_2025_festivos.csv",
        "fecha_carga": "2026-02-01T09:00:00Z",
        "registros_importados": 12,
        "hash": "abc123def456"
      }
    ]
  }
}
```

---

### 1.5 Formato CSV Esperado

```csv
fecha,tipo,titulo,descripcion,categoria
2025-11-01,festivo,Todos los Santos,Festivo nacional,festivo_nacional
2025-12-06,festivo,Constitución,Festivo nacional,festivo_nacional
2025-12-25,festivo,Navidad,Festivo nacional,festivo_nacional
2026-01-15,evento,Mantenimiento programado,Actualización servidores,operacional
2026-02-10,deadline,Entrega Q1,Cierre trimestre,negocio
```

**Columnas requeridas:**
- `fecha` (YYYY-MM-DD) - Obligatorio
- `tipo` (festivo|evento|deadline|otro) - Obligatorio
- `titulo` - Obligatorio
- `descripcion` - Opcional
- `categoria` - Opcional

---

### 1.6 Implementación Detallada

#### 1.6.1 Clase CalendarManager
```python
class CalendarManager:
    """Gestor de calendarios históricos y futuros"""
    
    def __init__(self, data_file: str = "json/calendarios.json"):
        self.data_file = data_file
        self.data = self._load_data()
        
    def import_csv(self, filepath: str) -> dict:
        """Importa eventos desde CSV"""
        # Validación de formato
        # Detección de duplicados
        # Merge con datos existentes
        # Retorna estadísticas de importación
        
    def get_month_view(self, year: int, month: int) -> dict:
        """Obtiene vista de un mes específico"""
        
    def get_multi_month_view(self, start_month: tuple, months: int) -> list:
        """Obtiene vista de múltiples meses consecutivos"""
        
    def add_event(self, fecha: str, evento: dict):
        """Añade evento manualmente"""
        
    def export_to_csv(self, start_date: str, end_date: str) -> str:
        """Exporta rango de fechas a CSV"""
```

#### 1.6.2 Componente UI - MultiMonthCalendar
```python
class MultiMonthCalendar(tk.Frame):
    """Widget para mostrar múltiples meses en grid"""
    
    def __init__(self, parent, months_before=3, months_after=3):
        self.months_before = months_before
        self.months_after = months_after
        self.current_reference = datetime.now()
        
    def render_timeline(self):
        """Renderiza línea de tiempo con 7 meses"""
        # Grid de 7 calendarios mensuales
        # Navegación con flechas
        # Highlighting del mes actual
        
    def on_date_click(self, date: datetime):
        """Handler de click en fecha"""
        # Muestra detalles en panel inferior
        
    def scroll_timeline(self, direction: int):
        """Desplaza timeline adelante/atrás"""
```

---

### 1.7 Decisión: Pestaña vs Modal

#### Comparativa

| Criterio | Pestaña Nueva | Modal Grande |
|----------|---------------|--------------|
| **Espacio visual** | ⭐⭐⭐⭐⭐ Máximo | ⭐⭐⭐ Limitado |
| **Contexto preservado** | ✅ Sí | ❌ Bloquea otras tabs |
| **Acceso rápido** | ✅ Un click | ⚠️ Requiere abrir |
| **Complejidad implementación** | ⭐⭐ Baja | ⭐⭐⭐ Media |
| **UX coherente** | ✅ Consistente | ⚠️ Diferente patrón |

**RECOMENDACIÓN:** **Pestaña nueva** (`TabCalendario`)

**Razones:**
1. Funcionalidad de consulta frecuente → merece espacio permanente
2. Coherencia con arquitectura actual (TabGenerador, TabVacios, TabLog)
3. Permite trabajo paralelo (consultar calendario mientras generas informe)
4. Escalabilidad: futuras features (eventos recurrentes, recordatorios)

---

### 1.8 Plan de Implementación (Sprints)

#### Sprint 1: Fundamentos (5-7 días)
- [ ] Crear `CalendarManager` con persistencia JSON
- [ ] Implementar importación CSV básica
- [ ] Crear `TabCalendario` con estructura base
- [ ] Vista single-month funcional

#### Sprint 2: Multi-month View (5-7 días)
- [ ] Componente `MultiMonthCalendar` (7 meses grid)
- [ ] Navegación temporal (scroll adelante/atrás)
- [ ] Panel de detalles del día seleccionado
- [ ] Integración con datos reales

#### Sprint 3: Features Avanzadas (3-5 días)
- [ ] Filtros por categoría/tipo
- [ ] Exportación a CSV
- [ ] Estadísticas mensuales
- [ ] Búsqueda de eventos
- [ ] Indicadores visuales (carga trabajo, festivos)

#### Sprint 4: Polish & Testing (2-3 días)
- [ ] Testing de importación CSV
- [ ] Manejo de errores robusto
- [ ] Documentación de usuario
- [ ] Performance optimization

**Total estimado:** 15-22 días laborables

---

### 1.9 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| CSV mal formateado | Alta | Medio | Validación estricta + UI de errores |
| Performance con muchos eventos | Media | Alto | Paginación + lazy loading |
| Conflictos de merge CSV | Media | Medio | Estrategia de resolución configurable |
| Tamaño JSON excesivo | Baja | Alto | Compresión + archivado por año |

---

## 🔌 PARTE 2: INTEGRACIÓN CON GOOGLE CALENDAR

### 2.1 Viabilidad Técnica: ✅ TOTALMENTE FACTIBLE

Google Calendar API está madura, bien documentada y Python tiene SDK oficial.

---

### 2.2 Arquitectura de Integración

```
┌──────────────────────────────────────────────────────────────┐
│               Freshdesk Reports Creator                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           TabCalendario / CalendarManager              │  │
│  └────────────────┬───────────────────────────────────────┘  │
│                   │                                          │
│                   │ eventos locales                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        GoogleCalendarSync (Nuevo Módulo)               │  │
│  │  • Autenticación OAuth 2.0                             │  │
│  │  • Sincronización bidireccional                        │  │
│  │  • Detección de conflictos                             │  │
│  │  • Rate limiting                                       │  │
│  └────────────────┬───────────────────────────────────────┘  │
└───────────────────┼───────────────────────────────────────────┘
                    │
                    │ HTTPS / OAuth 2.0
                    ▼
     ┌──────────────────────────────────┐
     │    Google Calendar API v3         │
     │  • events.insert()                │
     │  • events.update()                │
     │  • events.delete()                │
     │  • events.list()                  │
     └──────────────────────────────────┘
```

---

### 2.3 Stack Tecnológico

```python
# Bibliotecas requeridas
google-auth                 # Autenticación OAuth 2.0
google-auth-oauthlib       # Flow de autenticación
google-auth-httplib2       # Transporte HTTP
google-api-python-client   # SDK de Google Calendar API
```

**Instalación:**
```bash
pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

### 2.4 Proceso de Autenticación OAuth 2.0

#### Flujo de Configuración (One-time Setup)

1. **Crear Proyecto en Google Cloud Console**
   - URL: https://console.cloud.google.com
   - Crear nuevo proyecto: "FreshdeskReportsCalendar"
   
2. **Habilitar Google Calendar API**
   - APIs & Services → Enable APIs → Google Calendar API

3. **Crear Credenciales OAuth 2.0**
   - Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download JSON → guardar como `credentials.json`

4. **Configurar Scopes**
   ```python
   SCOPES = ['https://www.googleapis.com/auth/calendar']
   # Permiso total para gestionar calendarios
   ```

#### Flujo de Usuario (Primera Vez)

```
Usuario → Click "Conectar Google Calendar"
       ↓
Se abre navegador → Login Google
       ↓
Autoriza permisos → Redirect con código
       ↓
App intercambia código por token
       ↓
Token guardado localmente (token.json)
       ↓
Conexión establecida ✅
```

**Subsecuentes ejecuciones:** Token se refresca automáticamente

---

### 2.5 Implementación Detallada

#### 2.5.1 Clase GoogleCalendarSync

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import json

class GoogleCalendarSync:
    """Sincronizador bidireccional con Google Calendar"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    TOKEN_FILE = 'json/google_token.json'
    CREDENTIALS_FILE = 'json/google_credentials.json'
    
    def __init__(self):
        self.service = None
        self.calendar_id = None  # ID del calendario destino
        self._authenticate()
        
    def _authenticate(self):
        """Realiza autenticación OAuth 2.0"""
        creds = None
        
        # Token ya existe
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(
                self.TOKEN_FILE, self.SCOPES
            )
        
        # Token expirado o no existe
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refrescar token
                creds.refresh(Request())
            else:
                # Nuevo flujo de autenticación
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Guardar token
            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        # Crear servicio
        self.service = build('calendar', 'v3', credentials=creds)
        
    def create_or_get_calendar(self, name: str = "Freshdesk Reports") -> str:
        """Crea o obtiene calendario dedicado"""
        # Buscar calendario existente
        calendars = self.service.calendarList().list().execute()
        
        for cal in calendars.get('items', []):
            if cal['summary'] == name:
                return cal['id']
        
        # Crear nuevo calendario
        calendar = {
            'summary': name,
            'description': 'Calendario generado automáticamente desde Freshdesk Reports Creator',
            'timeZone': 'Europe/Madrid'
        }
        
        created = self.service.calendars().insert(body=calendar).execute()
        return created['id']
        
    def sync_event(self, evento: dict) -> dict:
        """
        Sincroniza un evento local a Google Calendar
        
        Args:
            evento: Diccionario con estructura:
                {
                    'titulo': str,
                    'descripcion': str,
                    'fecha': 'YYYY-MM-DD',
                    'tipo': str,
                    'google_event_id': str (opcional, para updates)
                }
        
        Returns:
            dict: Evento creado/actualizado con google_event_id
        """
        # Construir evento en formato Google Calendar
        event_body = {
            'summary': evento['titulo'],
            'description': evento.get('descripcion', ''),
            'start': {
                'date': evento['fecha'],  # All-day event
            },
            'end': {
                'date': evento['fecha'],
            },
            'colorId': self._get_color_id(evento.get('tipo')),
            'source': {
                'title': 'Freshdesk Reports Creator',
                'url': 'https://freshdesk.com'
            }
        }
        
        # Update vs Create
        if 'google_event_id' in evento and evento['google_event_id']:
            # Actualizar evento existente
            result = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=evento['google_event_id'],
                body=event_body
            ).execute()
        else:
            # Crear nuevo evento
            result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()
        
        return {
            'google_event_id': result['id'],
            'link': result.get('htmlLink')
        }
        
    def sync_bulk(self, eventos: list, progress_callback=None) -> dict:
        """
        Sincroniza múltiples eventos en batch
        
        Args:
            eventos: Lista de eventos a sincronizar
            progress_callback: Función para reportar progreso
            
        Returns:
            dict: Estadísticas de sincronización
        """
        stats = {
            'total': len(eventos),
            'created': 0,
            'updated': 0,
            'errors': 0,
            'errores': []
        }
        
        for i, evento in enumerate(eventos):
            try:
                result = self.sync_event(evento)
                
                if 'google_event_id' in evento:
                    stats['updated'] += 1
                else:
                    stats['created'] += 1
                
                # Actualizar evento local con google_event_id
                evento['google_event_id'] = result['google_event_id']
                
                if progress_callback:
                    progress_callback(i + 1, len(eventos))
                    
            except Exception as e:
                stats['errors'] += 1
                stats['errores'].append({
                    'evento': evento.get('titulo'),
                    'error': str(e)
                })
                
        return stats
        
    def pull_updates(self, since: datetime) -> list:
        """
        Descarga cambios desde Google Calendar (sincronización inversa)
        
        Args:
            since: Fecha desde la cual buscar cambios
            
        Returns:
            list: Eventos modificados en Google Calendar
        """
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=since.isoformat() + 'Z',
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
        
    def delete_event(self, google_event_id: str):
        """Elimina evento de Google Calendar"""
        self.service.events().delete(
            calendarId=self.calendar_id,
            eventId=google_event_id
        ).execute()
        
    def _get_color_id(self, tipo: str) -> str:
        """Mapea tipo de evento a color de Google Calendar"""
        color_map = {
            'festivo': '11',      # Rojo
            'deadline': '6',      # Naranja
            'evento': '9',        # Azul
            'mantenimiento': '8', # Gris
            'default': '1'        # Lavanda
        }
        return color_map.get(tipo, color_map['default'])
```

---

### 2.6 Integración en la UI

#### Botones en TabCalendario

```python
# En TabCalendario._create_widgets()

# Frame de sincronización
sync_frame = tk.Frame(self.control_panel, bg="#f5f5f5")
sync_frame.pack(fill="x", pady=10)

tk.Label(
    sync_frame, 
    text="🔄 Google Calendar Sync",
    font=("Arial", 10, "bold")
).pack(anchor="w")

# Estado de conexión
self.google_status_label = tk.Label(
    sync_frame,
    text="❌ No conectado",
    fg="#F44336"
)
self.google_status_label.pack(anchor="w", pady=5)

# Botones de acción
btn_container = tk.Frame(sync_frame, bg="#f5f5f5")
btn_container.pack(fill="x")

self.btn_connect_google = tk.Button(
    btn_container,
    text="🔌 Conectar Google Calendar",
    command=self._connect_google,
    bg="#4285F4",  # Google Blue
    fg="white",
    font=("Arial", 9, "bold")
)
self.btn_connect_google.pack(side="left", padx=5)

self.btn_sync_to_google = tk.Button(
    btn_container,
    text="☁️ Subir Eventos",
    command=self._sync_to_google,
    bg="#34A853",  # Google Green
    fg="white",
    font=("Arial", 9, "bold"),
    state="disabled"
)
self.btn_sync_to_google.pack(side="left", padx=5)

self.btn_pull_from_google = tk.Button(
    btn_container,
    text="⬇️ Descargar Cambios",
    command=self._pull_from_google,
    bg="#FBBC04",  # Google Yellow
    fg="black",
    font=("Arial", 9, "bold"),
    state="disabled"
)
self.btn_pull_from_google.pack(side="left", padx=5)
```

#### Handlers

```python
def _connect_google(self):
    """Conecta con Google Calendar"""
    try:
        self.main_app.log("🔌 Iniciando conexión con Google Calendar...", "info")
        
        # Inicializar sync (esto abre navegador si es necesario)
        self.google_sync = GoogleCalendarSync()
        
        # Crear o obtener calendario
        self.google_sync.calendar_id = self.google_sync.create_or_get_calendar()
        
        # Actualizar UI
        self.google_status_label.config(
            text=f"✅ Conectado - Calendario: Freshdesk Reports",
            fg="#4CAF50"
        )
        self.btn_sync_to_google.config(state="normal")
        self.btn_pull_from_google.config(state="normal")
        self.btn_connect_google.config(state="disabled")
        
        self.main_app.log("✅ Conexión establecida con Google Calendar", "success")
        
    except Exception as e:
        self.main_app.log(f"❌ Error conectando: {str(e)}", "error")
        messagebox.showerror("Error", f"No se pudo conectar:\n{str(e)}")

def _sync_to_google(self):
    """Sincroniza eventos locales a Google Calendar"""
    try:
        # Obtener eventos locales
        eventos = self.calendar_manager.get_all_events()
        
        if not eventos:
            messagebox.showinfo("Info", "No hay eventos para sincronizar")
            return
        
        # Confirmar
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Subir {len(eventos)} eventos a Google Calendar?"
        ):
            return
        
        # Crear ventana de progreso
        progress_window = tk.Toplevel(self)
        progress_window.title("Sincronizando...")
        progress_window.geometry("400x150")
        
        progress_label = tk.Label(progress_window, text="Sincronizando eventos...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(
            progress_window,
            length=300,
            mode='determinate'
        )
        progress_bar.pack(pady=10)
        
        stats_label = tk.Label(progress_window, text="")
        stats_label.pack()
        
        def update_progress(current, total):
            progress_bar['value'] = (current / total) * 100
            stats_label.config(text=f"{current} / {total}")
            progress_window.update()
        
        # Ejecutar sincronización
        stats = self.google_sync.sync_bulk(eventos, update_progress)
        
        progress_window.destroy()
        
        # Mostrar resultados
        mensaje = f"""
Sincronización completada:

✅ Creados: {stats['created']}
🔄 Actualizados: {stats['updated']}
❌ Errores: {stats['errors']}
        """
        
        if stats['errors'] > 0:
            mensaje += f"\n\nErrores:\n"
            for err in stats['errores'][:5]:
                mensaje += f"• {err['evento']}: {err['error']}\n"
        
        # Guardar cambios (eventos ahora tienen google_event_id)
        self.calendar_manager.save_data()
        
        self.main_app.log(
            f"✅ Sincronización: {stats['created']} creados, {stats['updated']} actualizados",
            "success"
        )
        
        messagebox.showinfo("Completado", mensaje)
        
    except Exception as e:
        self.main_app.log(f"❌ Error en sincronización: {str(e)}", "error")
        messagebox.showerror("Error", f"Error al sincronizar:\n{str(e)}")
```

---

### 2.7 Modos de Sincronización

#### Modo 1: Manual (MVP)
- Usuario hace click en "☁️ Subir Eventos"
- Sincroniza todos los eventos locales
- Detecta cambios por última fecha de modificación

#### Modo 2: Automático (v2.0)
```python
class AutoSyncScheduler:
    """Sincronización automática en background"""
    
    def __init__(self, sync: GoogleCalendarSync, interval_minutes: int = 30):
        self.sync = sync
        self.interval = interval_minutes * 60  # a segundos
        self.running = False
        
    def start(self):
        """Inicia sincronización automática"""
        self.running = True
        threading.Thread(target=self._sync_loop, daemon=True).start()
        
    def _sync_loop(self):
        """Loop de sincronización"""
        while self.running:
            try:
                # Sincronizar cambios locales → Google
                # Sincronizar cambios Google → local
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error en auto-sync: {e}")
```

#### Modo 3: Bidireccional (v3.0)
- Detecta cambios en ambas direcciones
- Resuelve conflictos (última modificación gana)
- Notificaciones de cambios externos

---

### 2.8 Requisitos Previos para Google Calendar API

#### Checklist de Configuración

- [ ] **Cuenta de Google Cloud:** Crear proyecto en https://console.cloud.google.com
- [ ] **Google Calendar API habilitada:** En "APIs & Services"
- [ ] **Credenciales OAuth 2.0:** Descargar `credentials.json`
- [ ] **Consent Screen configurado:** Información de la app
- [ ] **Scope de Calendar:** `https://www.googleapis.com/auth/calendar`
- [ ] **Archivo credentials.json:** Guardar en `json/google_credentials.json`

#### Limitaciones y Cuotas

| Límite | Valor | Implicación |
|--------|-------|-------------|
| Requests/día | 1,000,000 | ✅ Más que suficiente |
| Requests/segundo | 10 | ⚠️ Implementar rate limiting |
| Eventos/batch | 1,000 | ✅ Perfecto para bulk sync |

**No hay costo** para uso básico dentro de cuotas gratuitas.

---

### 2.9 Seguridad y Privacidad

#### Almacenamiento de Tokens
```python
# json/google_token.json
{
  "token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0gZ3...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "123456789.apps.googleusercontent.com",
  "client_secret": "GOCSPX-...",
  "scopes": ["https://www.googleapis.com/auth/calendar"],
  "expiry": "2026-02-02T11:30:00.000000Z"
}
```

**⚠️ IMPORTANTE:** Añadir a `.gitignore`:
```
json/google_token.json
json/google_credentials.json
```

#### Permisos Solicitados
- **Scope:** `https://www.googleapis.com/auth/calendar`
- **Acceso:** Lectura y escritura total de calendarios
- **Revocación:** Usuario puede revocar desde cuenta Google

---

### 2.10 Testing y Validación

#### Test Suite Recomendado

```python
# tests/test_google_sync.py

class TestGoogleCalendarSync:
    
    def test_authentication(self):
        """Verifica flujo de autenticación"""
        sync = GoogleCalendarSync()
        assert sync.service is not None
        
    def test_create_calendar(self):
        """Crea calendario de prueba"""
        sync = GoogleCalendarSync()
        cal_id = sync.create_or_get_calendar("Test Calendar")
        assert cal_id is not None
        
    def test_sync_single_event(self):
        """Sincroniza un evento"""
        sync = GoogleCalendarSync()
        evento = {
            'titulo': 'Test Event',
            'descripcion': 'Test',
            'fecha': '2026-03-15',
            'tipo': 'evento'
        }
        result = sync.sync_event(evento)
        assert 'google_event_id' in result
        
    def test_sync_bulk(self):
        """Sincroniza múltiples eventos"""
        # Crear 10 eventos de prueba
        # Verificar stats
        
    def test_pull_updates(self):
        """Descarga cambios desde Google"""
        # Modificar evento en Google Calendar manualmente
        # Verificar que pull_updates lo detecta
```

---

### 2.11 Roadmap de Integración

#### Fase 1: MVP (1 semana)
- [x] Análisis y diseño
- [ ] Setup de Google Cloud Project
- [ ] Implementar `GoogleCalendarSync` básico
- [ ] Autenticación OAuth 2.0
- [ ] Sync unidireccional (local → Google)
- [ ] UI de conexión en `TabCalendario`

#### Fase 2: Mejoras (3-5 días)
- [ ] Sincronización bidireccional
- [ ] Detección de conflictos
- [ ] Bulk sync optimizado
- [ ] Progress indicators

#### Fase 3: Avanzado (1 semana)
- [ ] Auto-sync en background
- [ ] Notificaciones de cambios
- [ ] Múltiples calendarios
- [ ] Filtros de sincronización selectiva
- [ ] Logs de sincronización

---

## 💰 Análisis Costo-Beneficio

### Costos

| Concepto | Estimación |
|----------|------------|
| **Desarrollo Gestor Calendarios** | 15-22 días |
| **Desarrollo Integración Google** | 7-10 días |
| **Testing y QA** | 3-5 días |
| **Documentación** | 2-3 días |
| **Total** | **27-40 días** |
| **Costo Google Cloud** | **$0** (dentro de free tier) |

### Beneficios

1. **Productividad:** -60% tiempo en planificación manual
2. **Visibilidad:** Vista unificada histórico + futuro
3. **Integración:** Calendarios en ecosistema Google Workspace
4. **Automatización:** Sincronización automática
5. **Trazabilidad:** Histórico completo de eventos

**ROI estimado:** Positivo a partir del mes 3

---

## 🎯 Recomendaciones Finales (CTO Perspective)

### ✅ GO FORWARD

**Prioridad 1: Gestor de Calendarios**
- Funcionalidad core con alto valor
- Sin dependencias externas críticas
- Quick win para usuarios

**Prioridad 2: Google Calendar Integration**
- Alto valor agregado
- Riesgo técnico bajo
- Ecosistema maduro

### 📋 Plan de Ejecución Propuesto

**Mes 1:**
- Sprint 1-2: Gestor de Calendarios (MVP)
- Sprint 3: Testing y refinamiento

**Mes 2:**
- Sprint 4: Google Calendar Integration (MVP)
- Sprint 5: Features avanzadas
- Sprint 6: Testing end-to-end

**Mes 3:**
- Sprint 7: Auto-sync y polish
- Sprint 8: Documentación y training

### ⚠️ Alertas Técnicas

1. **Rate Limiting:** Implementar desde día 1 para Google API
2. **Token Refresh:** Manejar expiración elegantemente
3. **Error Handling:** Red robusta de try-catch
4. **Data Validation:** CSV pueden venir con basura
5. **Performance:** Lazy loading para históricos grandes

### 🔮 Visión a Futuro

**v2.0 Potenciales:**
- Recordatorios por email
- Eventos recurrentes
- Integración con Freshdesk (tickets → eventos)
- Analytics predictivo de carga de trabajo
- Export a formatos múltiples (iCal, Outlook)

---

## 📞 Next Steps

1. **Validar con stakeholders:** Priorizar features
2. **Setup Google Cloud Project:** Hoy mismo
3. **Crear spike técnico:** 2 días para PoC de calendario multi-mes
4. **Aprobar roadmap:** Antes de iniciar Sprint 1

---

**Documentado por:** CTO & Senior Integration Architect  
**Fecha:** 2 de febrero de 2026  
**Estado:** ✅ Ready for Implementation
