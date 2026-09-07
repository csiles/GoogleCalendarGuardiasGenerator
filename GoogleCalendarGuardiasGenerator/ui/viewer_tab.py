"""
Pestaña de visualización de calendarios históricos y futuros
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import re
import threading
import logging
from models.calendar_manager import CalendarManager
from ui.components.multi_month_viewer import MultiMonthViewer
from ui.dialogs.calendar_config_dialog import CalendarConfigDialog
from utils.file_utils import get_technician_colors, load_tecnicos
from utils.google_calendar_sync import GoogleCalendarSync

logger = logging.getLogger(__name__)


class ViewerTab(tk.Frame):
    """Pestaña para visualizar calendarios históricos"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Cargar colores de técnicos
        self.colors = get_technician_colors()
        
        # Cargar lista de técnicos
        self.tecnicos = load_tecnicos()
        
        # Técnico seleccionado para drag
        self.selected_tecnico = None
        
        # Inicializar CalendarManager
        self.calendar_manager = CalendarManager()
        
        # Inicializar Google Calendar Sync
        self.google_sync = GoogleCalendarSync()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets de la interfaz"""
        self._create_header()
        self._create_toolbar()
        self._create_viewer()
        self._create_status_bar()
    
    def _create_header(self):
        """Crea el encabezado de la pestaña"""
        header = tk.Frame(self, bg="#2c3e50", height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="Visualizador de Calendarios", 
                font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(pady=10)
    
    def _create_toolbar(self):
        """Crea la barra de herramientas"""
        toolbar = tk.Frame(self, bg="#34495e", height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # 3 columnas: izquierda fija, centro fijo, dos huecos elásticos para centrar el grupo de botones
        toolbar.grid_columnconfigure(0, weight=0)
        toolbar.grid_columnconfigure(1, weight=1)
        toolbar.grid_columnconfigure(2, weight=0)
        toolbar.grid_columnconfigure(3, weight=1)
        
        # Frame izquierdo: estado del calendario configurado + botón de login
        left_frame = tk.Frame(toolbar, bg="#34495e")
        left_frame.grid(row=0, column=0, sticky="w", padx=10)
        
        self.lbl_calendar_selected = tk.Label(left_frame, text="Calendario seleccionado: No configurado",
                bg="#34495e", fg="white", font=("Arial", 10))
        self.lbl_calendar_selected.pack(side=tk.LEFT, padx=(0, 8))
        
        self.btn_config_google = tk.Button(left_frame, text="Login/config", command=self._configure_google,
                 bg="#9b59b6", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5)
        self.btn_config_google.pack(side=tk.LEFT)
        
        # Frame central: acciones principales, centrado en la toolbar
        btn_frame = tk.Frame(toolbar, bg="#34495e")
        btn_frame.grid(row=0, column=2, pady=10)
        
        # Botón importar CSV
        tk.Button(btn_frame, text="Importar CSV", command=self._import_csv,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Botón actualizar
        tk.Button(btn_frame, text="Actualizar", command=self._refresh_view,
                 bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Separador
        tk.Frame(btn_frame, width=20, bg="#34495e").pack(side=tk.LEFT)
        
        # Botón sincronizar: local -> Google
        self.btn_sync_to_google = tk.Button(btn_frame, text="Sincro: Local → Google", command=self._sync_to_google,
                 bg="#e67e22", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5)
        self.btn_sync_to_google.pack(side=tk.LEFT, padx=5)
        
        # Botón sincronizar: Google -> local
        self.btn_sync_from_google = tk.Button(btn_frame, text="Sincro: Google → Local", command=self._sync_from_google,
                 bg="#16a085", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5)
        self.btn_sync_from_google.pack(side=tk.LEFT, padx=5)
        
        # Actualizar estado de botones según configuración
        self._update_google_buttons_state()
    
    def _create_viewer(self):
        """Crea el visor de múltiples meses"""
        viewer_container = tk.Frame(self, bg="#ecf0f1")
        viewer_container.pack(fill=tk.BOTH, expand=True)
        
        # Crear el componente de visualización
        self.multi_month_viewer = MultiMonthViewer(
            viewer_container,
            self.calendar_manager,
            colors=self.colors,
            num_months=7,
            parent_tab=self  # Pasar referencia para callbacks
        )
        self.multi_month_viewer.pack(fill=tk.BOTH, expand=True)
    
    def _start_drag(self, tecnico):
        """Inicia el drag de un técnico"""
        self.selected_tecnico = tecnico
        self.multi_month_viewer.set_dragging_tecnico(tecnico)
    
    def _end_drag(self):
        """Finaliza el drag"""
        self.selected_tecnico = None
        self.multi_month_viewer.set_dragging_tecnico(None)
    
    def _create_status_bar(self):
        """Crea la barra de estado"""
        status_bar = tk.Frame(self, bg="#2c3e50", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(status_bar, text="Listo", 
                                     font=("Arial", 9), bg="#2c3e50", fg="white",
                                     anchor="w", padx=10)
        self.status_label.pack(fill=tk.X)
        
        self._update_status()
    
    def _import_csv(self):
        """Importa eventos desde un archivo CSV"""
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            stats = self.calendar_manager.import_csv(filepath)
            
            mensaje = f"✅ Importación completada\n\n"
            mensaje += f"Total registros: {stats['total']}\n"
            mensaje += f"Importados: {stats['importados']}\n"
            mensaje += f"Duplicados: {stats['duplicados']}\n"
            mensaje += f"Errores: {stats['errores']}"
            
            if stats['errores'] > 0 and stats['errores_detalle']:
                mensaje += f"\n\nPrimeros errores:\n"
                for err in stats['errores_detalle'][:3]:
                    mensaje += f"- Fila {err.get('fila', '?')}: {err.get('error', 'Error desconocido')}\n"
            
            messagebox.showinfo("Importación completada", mensaje)
            
            # Actualizar vista
            self._refresh_view()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al importar CSV:\n{str(e)}")
    
    def _refresh_view(self):
        """Actualiza la visualización"""
        self.multi_month_viewer.reset_to_today()
        self._update_status()
    
    def _update_status(self):
        """Actualiza la barra de estado"""
        stats = self.calendar_manager.get_statistics()
        google_status = ""
        
        if self.google_sync.is_configured():
            config = self.google_sync.get_config()
            google_status = f" | Google: {config.get('calendar_name', 'Configurado')}"
        else:
            google_status = " | Google: No configurado"
        
        text = f"Total eventos: {stats['total_eventos']} | Meses: {stats['total_meses_con_datos']} | Última actualización: {stats['ultima_actualizacion'][:19]}{google_status}"
        self.status_label.config(text=text)
    
    def _update_google_buttons_state(self):
        """Actualiza el estado de los botones de Google según configuración"""
        if self.google_sync.is_configured():
            self.btn_sync_to_google.config(state=tk.NORMAL)
            self.btn_sync_from_google.config(state=tk.NORMAL)
            config = self.google_sync.get_config()
            self.lbl_calendar_selected.config(text=f"Calendario seleccionado: {config.get('calendar_name', 'Configurado')}")
        else:
            self.btn_sync_to_google.config(state=tk.DISABLED)
            self.btn_sync_from_google.config(state=tk.DISABLED)
            self.lbl_calendar_selected.config(text="Calendario seleccionado: No configurado")
    
    def _configure_google(self):
        """Abre diálogo de configuración de Google Calendar"""
        try:
            dialog = CalendarConfigDialog(self, self.google_sync)
            self.wait_window(dialog)
            
            # Actualizar estado de botones
            self._update_google_buttons_state()
            self._update_status()
            
        except Exception as e:
            logger.error(f"Error configurando Google Calendar: {e}")
            messagebox.showerror(
                "Error de configuración",
                f"Error al configurar Google Calendar:\n\n{str(e)}\n\n"
                "Verifica que el archivo json/google_credentials.json esté presente."
            )
    
    def _sync_to_google(self):
        """Sincroniza eventos: local -> Google Calendar"""
        if not self.google_sync.is_configured():
            messagebox.showwarning(
                "No configurado",
                "Primero debes configurar el calendario de Google.\n"
                "Haz clic en 'Login/config'."
            )
            return
        
        # Confirmar
        confirm = messagebox.askyesno(
            "Confirmar sincronización",
            "¿Deseas sincronizar todas las guardias locales hacia Google Calendar?\n\n"
            "Esto creará/actualizará los eventos en el calendario configurado."
        )
        
        if not confirm:
            return
        
        # Obtener todos los eventos
        eventos = self.calendar_manager.get_all_events()
        
        if not eventos:
            messagebox.showinfo("Sin eventos", "No hay eventos para sincronizar.")
            return
        
        # Deshabilitar botones durante sincronización
        self.btn_sync_to_google.config(state=tk.DISABLED, text="Sincronizando...")
        self.btn_sync_from_google.config(state=tk.DISABLED)
        self.btn_config_google.config(state=tk.DISABLED)
        
        # Crear ventana de progreso
        progress_window = self._create_progress_window()
        
        # Ejecutar sincronización en thread
        def sync_thread():
            try:
                # Autenticar si es necesario
                if not self.google_sync.service:
                    self.after(0, lambda: self._update_progress(progress_window, "Autenticando con Google..."))
                    self.google_sync.authenticate()
                
                # Preparar eventos para sincronización
                eventos_sync = []
                for evento in eventos:
                    evento_sync = {
                        'titulo': evento.get('titulo', 'Guardia'),
                        'descripcion': evento.get('descripcion', ''),
                        'fecha': evento.get('fecha'),
                        'tipo': evento.get('tipo', 'guardia'),
                        'color': self.colors.get(evento.get('titulo', '').split()[0], None),
                        'google_event_id': evento.get('google_event_id')
                    }
                    eventos_sync.append(evento_sync)
                
                # Callback de progreso
                def progress_callback(current, total, evento_nombre):
                    percent = int((current / total) * 100)
                    self.after(0, lambda: self._update_progress(
                        progress_window, 
                        f"Sincronizando {current}/{total} ({percent}%)\n{evento_nombre}"
                    ))
                
                # Sincronizar
                stats = self.google_sync.sync_bulk(eventos_sync, progress_callback)
                
                # Actualizar google_event_id en CalendarManager
                for evento_sync in eventos_sync:
                    if evento_sync.get('google_event_id'):
                        # Encontrar evento original y actualizar
                        for evento in eventos:
                            if evento.get('fecha') == evento_sync.get('fecha') and \
                               evento.get('titulo') == evento_sync.get('titulo'):
                                self.calendar_manager.update_google_event_id(
                                    evento['fecha'],
                                    evento['id'],
                                    evento_sync['google_event_id'],
                                    evento_sync.get('google_link')
                                )
                                break
                
                # Guardar cambios
                self.calendar_manager.save_data()
                
                # Mostrar resultados
                self.after(0, lambda: self._show_sync_results(stats, progress_window))
                
            except Exception as e:
                logger.error(f"Error en sincronización: {e}")
                self.after(0, lambda: self._show_sync_error(str(e), progress_window))
            finally:
                # Rehabilitar botones
                self.after(0, lambda: self.btn_sync_to_google.config(state=tk.NORMAL, text="Sincro: Local → Google"))
                self.after(0, lambda: self.btn_sync_from_google.config(state=tk.NORMAL))
                self.after(0, lambda: self.btn_config_google.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=sync_thread, daemon=True)
        thread.start()
    
    def _get_pull_date_range(self):
        """Calcula el rango de fechas a descargar desde Google: el mismo que cubren los datos locales,
        o una ventana por defecto si no hay datos locales todavía"""
        meses = self.calendar_manager.data.get('meses', {})
        if meses:
            keys = sorted(meses.keys())
            start = datetime.strptime(f"{keys[0]}-01", "%Y-%m-%d")
            end_year, end_month = map(int, keys[-1].split('-'))
            if end_month == 12:
                end = datetime(end_year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(end_year, end_month + 1, 1) - timedelta(days=1)
        else:
            start = datetime.now() - timedelta(days=30)
            end = datetime.now() + timedelta(days=180)
        return start, end
    
    def _sync_from_google(self):
        """Sincroniza eventos: Google Calendar -> local"""
        if not self.google_sync.is_configured():
            messagebox.showwarning(
                "No configurado",
                "Primero debes configurar el calendario de Google.\n"
                "Haz clic en 'Login/config'."
            )
            return
        
        time_min, time_max = self._get_pull_date_range()
        
        confirm = messagebox.askyesno(
            "Confirmar sincronización",
            "¿Deseas descargar los eventos de Google Calendar hacia el calendario local?\n\n"
            f"Rango: {time_min.strftime('%Y-%m-%d')} a {time_max.strftime('%Y-%m-%d')}\n"
            "Los eventos que no coincidan con un técnico conocido te serán preguntados uno a uno."
        )
        
        if not confirm:
            return
        
        self.btn_sync_to_google.config(state=tk.DISABLED)
        self.btn_sync_from_google.config(state=tk.DISABLED, text="Sincronizando...")
        self.btn_config_google.config(state=tk.DISABLED)
        
        progress_window = self._create_progress_window()
        
        def pull_thread():
            try:
                if not self.google_sync.service:
                    self.after(0, lambda: self._update_progress(progress_window, "Autenticando con Google..."))
                    self.google_sync.authenticate()
                
                self.after(0, lambda: self._update_progress(progress_window, "Descargando eventos de Google Calendar..."))
                eventos_google = self.google_sync.pull_events(time_min, time_max)
                
                self.after(0, lambda: self._process_pulled_events(eventos_google, progress_window))
                
            except Exception as e:
                logger.error(f"Error descargando eventos de Google: {e}")
                self.after(0, lambda: self._show_sync_error(str(e), progress_window))
                self.after(0, lambda: self.btn_sync_to_google.config(state=tk.NORMAL))
                self.after(0, lambda: self.btn_sync_from_google.config(state=tk.NORMAL, text="Sincro: Google → Local"))
                self.after(0, lambda: self.btn_config_google.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=pull_thread, daemon=True)
        thread.start()
    
    def _process_pulled_events(self, eventos_google, progress_window):
        """Clasifica los eventos descargados de Google e importa al calendario local.
        Los que no coincidan con ningún técnico conocido se preguntan uno a uno."""
        if progress_window.winfo_exists():
            progress_window.destroy()
        
        importados_reconocidos = 0
        importados_genericos = 0
        omitidos = 0
        stop_asking = False
        
        for evento_google in eventos_google:
            fecha = evento_google.get('fecha')
            titulo = evento_google.get('titulo', 'Sin título')
            if not fecha:
                continue
            
            match = re.match(r'^Guardia\s*-\s*(.+)$', titulo.strip())
            tecnico_detectado = match.group(1).strip() if match else None
            
            if tecnico_detectado and tecnico_detectado in self.tecnicos:
                tecnico = tecnico_detectado
                tipo = 'guardia'
            elif stop_asking:
                omitidos += 1
                continue
            else:
                respuesta = messagebox.askyesnocancel(
                    "Evento no reconocido",
                    f"El evento de Google '{titulo}' del {fecha} no coincide con ningún técnico conocido.\n\n"
                    "Sí = importarlo como evento genérico\n"
                    "No = omitir solo este evento\n"
                    "Cancelar = omitir este y el resto de eventos no reconocidos"
                )
                if respuesta is None:
                    stop_asking = True
                    omitidos += 1
                    continue
                elif respuesta is False:
                    omitidos += 1
                    continue
                else:
                    tecnico = None
                    tipo = 'otro'
            
            evento_local = {
                'id': self.calendar_manager._generate_event_id(fecha, titulo),
                'titulo': titulo,
                'descripcion': evento_google.get('descripcion', ''),
                'tecnico': tecnico,
                'tipo': tipo,
                'origen': 'google_pull',
                'google_event_id': evento_google.get('google_event_id'),
                'google_link': evento_google.get('link')
            }
            
            added = self.calendar_manager.add_event(fecha, evento_local)
            if added:
                if tipo == 'guardia':
                    importados_reconocidos += 1
                else:
                    importados_genericos += 1
        
        self.calendar_manager.save_data()
        
        self.btn_sync_to_google.config(state=tk.NORMAL)
        self.btn_sync_from_google.config(state=tk.NORMAL, text="Sincro: Google → Local")
        self.btn_config_google.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "Sincronización completada",
            f"✅ Descarga desde Google Calendar completada\n\n"
            f"Total descargados: {len(eventos_google)}\n"
            f"Importados (técnico reconocido): {importados_reconocidos}\n"
            f"Importados (genéricos): {importados_genericos}\n"
            f"Omitidos: {omitidos}"
        )
        
        self._refresh_view()
    
    def _create_progress_window(self):
        """Crea ventana de progreso para sincronización"""
        progress_window = tk.Toplevel(self)
        progress_window.title("Sincronizando...")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Centrar
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(progress_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        progress_label = ttk.Label(frame, text="Iniciando sincronización...", font=("Segoe UI", 10))
        progress_label.pack(pady=(0, 10))
        
        progress_bar = ttk.Progressbar(frame, mode='indeterminate')
        progress_bar.pack(fill=tk.X, pady=10)
        progress_bar.start(10)
        
        # Guardar referencia a label
        progress_window.progress_label = progress_label
        
        return progress_window
    
    def _update_progress(self, progress_window, text):
        """Actualiza texto de progreso"""
        if progress_window.winfo_exists():
            progress_window.progress_label.config(text=text)
    
    def _show_sync_results(self, stats, progress_window):
        """Muestra resultados de sincronización"""
        if progress_window.winfo_exists():
            progress_window.destroy()
        
        mensaje = f"✅ Sincronización completada\n\n"
        mensaje += f"Total eventos: {stats['total']}\n"
        mensaje += f"Creados: {stats['created']}\n"
        mensaje += f"Actualizados: {stats['updated']}\n"
        mensaje += f"Errores: {stats['errors']}"
        
        if stats['errors'] > 0 and stats['errores_detalle']:
            mensaje += f"\n\nPrimeros errores:\n"
            for err in stats['errores_detalle'][:3]:
                mensaje += f"- {err.get('evento', '?')}: {err.get('error', 'Error desconocido')}\n"
        
        # Mostrar URL del calendario
        url = self.google_sync.get_calendar_url()
        if url:
            mensaje += f"\n\n🔗 Ver en Google Calendar:\n{url}"
        
        messagebox.showinfo("Sincronización completada", mensaje)
        
        # Actualizar vista
        self._refresh_view()
    
    def _show_sync_error(self, error_msg, progress_window):
        """Muestra error de sincronización"""
        if progress_window.winfo_exists():
            progress_window.destroy()
        
        messagebox.showerror(
            "Error de sincronización",
            f"Error al sincronizar con Google Calendar:\n\n{error_msg}"
        )
