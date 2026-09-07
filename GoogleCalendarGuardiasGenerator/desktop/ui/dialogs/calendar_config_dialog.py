"""
Diálogo de configuración de Google Calendar
Permite seleccionar calendario de Google (propio o compartido)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging

logger = logging.getLogger(__name__)


class CalendarConfigDialog(tk.Toplevel):
    """Diálogo para seleccionar calendario de Google"""
    
    def __init__(self, parent, google_sync):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Ventana padre
            google_sync: Instancia de GoogleCalendarSync
        """
        super().__init__(parent)
        
        self.google_sync = google_sync
        self.selected_calendar = None
        self.calendars = []
        
        self.title("Configurar Google Calendar")
        self.geometry("700x500")
        self.resizable(False, False)
        
        # Centrar en pantalla
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._start_loading()
        
    def _create_widgets(self):
        """Crea los widgets del diálogo"""
        
        # Frame principal
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="🗓️ Seleccionar Calendario de Google",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Instrucciones
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = (
            "Selecciona el calendario de Google donde quieres sincronizar las guardias.\n"
            "Puedes elegir tu calendario personal o cualquier calendario compartido "
            "donde tengas permisos de escritura."
        )
        info_label = ttk.Label(
            info_frame,
            text=info_text,
            wraplength=650,
            justify=tk.LEFT
        )
        info_label.pack()
        
        # Frame de carga
        self.loading_frame = ttk.Frame(main_frame)
        self.loading_frame.pack(fill=tk.BOTH, expand=True)
        
        loading_label = ttk.Label(
            self.loading_frame,
            text="⏳ Cargando calendarios disponibles...",
            font=("Segoe UI", 11)
        )
        loading_label.pack(pady=50)
        
        self.progress_bar = ttk.Progressbar(
            self.loading_frame,
            mode='indeterminate'
        )
        self.progress_bar.pack(pady=10, padx=50, fill=tk.X)
        self.progress_bar.start(10)
        
        # Frame de lista de calendarios (oculto inicialmente)
        self.calendars_frame = ttk.Frame(main_frame)
        
        # Listbox con scrollbar
        list_frame = ttk.Frame(self.calendars_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.calendars_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
            height=15,
            selectmode=tk.SINGLE,
            activestyle='none'
        )
        self.calendars_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.calendars_listbox.yview)
        
        # Bind doble click
        self.calendars_listbox.bind('<Double-Button-1>', lambda e: self._on_select())
        
        # Frame de detalles del calendario seleccionado
        self.details_frame = ttk.LabelFrame(self.calendars_frame, text="Detalles", padding="10")
        self.details_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.details_label = ttk.Label(
            self.details_frame,
            text="Selecciona un calendario para ver sus detalles",
            justify=tk.LEFT
        )
        self.details_label.pack()
        
        # Bind selección
        self.calendars_listbox.bind('<<ListboxSelect>>', self._on_calendar_selected)
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.select_button = ttk.Button(
            buttons_frame,
            text="✅ Seleccionar",
            command=self._on_select,
            state=tk.DISABLED
        )
        self.select_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_button = ttk.Button(
            buttons_frame,
            text="❌ Cancelar",
            command=self.destroy
        )
        cancel_button.pack(side=tk.RIGHT)
        
    def _start_loading(self):
        """Inicia la carga de calendarios en segundo plano"""
        thread = threading.Thread(target=self._load_calendars, daemon=True)
        thread.start()
        
    def _load_calendars(self):
        """Carga lista de calendarios desde Google (thread)"""
        try:
            # Autenticar si es necesario
            if not self.google_sync.service:
                self.google_sync.authenticate()
            
            # Obtener calendarios
            self.calendars = self.google_sync.list_available_calendars()
            
            # Actualizar UI en el thread principal
            self.after(0, self._show_calendars)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error cargando calendarios: {error_msg}")
            self.after(0, lambda msg=error_msg: self._show_error(msg))
            
    def _show_calendars(self):
        """Muestra la lista de calendarios en la UI"""
        # Ocultar loading
        self.progress_bar.stop()
        self.loading_frame.pack_forget()
        
        # Mostrar lista
        self.calendars_frame.pack(fill=tk.BOTH, expand=True)
        
        # Llenar listbox
        for i, cal in enumerate(self.calendars):
            # Formato: "📅 Nombre del Calendario (owner/writer) [PRIMARY]"
            icon = "👤" if cal['is_primary'] else "👥"
            role_icon = "🔒" if cal['access_role'] == 'owner' else "✏️"
            primary_tag = " [PRINCIPAL]" if cal['is_primary'] else ""
            
            display_text = f"{icon} {cal['name']} {role_icon}{primary_tag}"
            self.calendars_listbox.insert(tk.END, display_text)
            
            # Colorear según tipo
            if cal['is_primary']:
                self.calendars_listbox.itemconfig(i, {'bg': '#e3f2fd'})
            elif cal['access_role'] == 'owner':
                self.calendars_listbox.itemconfig(i, {'bg': '#f3e5f5'})
            else:
                self.calendars_listbox.itemconfig(i, {'bg': '#fff3e0'})
        
        # Si hay configuración previa, seleccionarla
        config = self.google_sync.get_config()
        if config and config.get('calendar_id'):
            for i, cal in enumerate(self.calendars):
                if cal['id'] == config['calendar_id']:
                    self.calendars_listbox.selection_set(i)
                    self.calendars_listbox.see(i)
                    break
                    
    def _show_error(self, error_msg: str):
        """Muestra error de carga"""
        self.progress_bar.stop()
        self.loading_frame.pack_forget()
        
        error_frame = ttk.Frame(self)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        error_label = ttk.Label(
            error_frame,
            text=f"❌ Error al cargar calendarios:\n\n{error_msg}",
            font=("Segoe UI", 11),
            foreground="red",
            wraplength=650
        )
        error_label.pack(pady=50)
        
        retry_button = ttk.Button(
            error_frame,
            text="🔄 Reintentar",
            command=self._retry_loading
        )
        retry_button.pack()
        
    def _retry_loading(self):
        """Reintenta cargar calendarios"""
        # Limpiar frames
        for widget in self.winfo_children():
            widget.destroy()
        
        # Recrear widgets
        self._create_widgets()
        self._start_loading()
        
    def _on_calendar_selected(self, event):
        """Maneja selección de calendario en la lista"""
        selection = self.calendars_listbox.curselection()
        if not selection:
            self.select_button.config(state=tk.DISABLED)
            self.details_label.config(text="Selecciona un calendario para ver sus detalles")
            return
        
        # Obtener calendario seleccionado
        index = selection[0]
        cal = self.calendars[index]
        
        # Mostrar detalles
        details_text = (
            f"📛 Nombre: {cal['name']}\n"
            f"🔑 Permisos: {cal['access_role'].upper()}\n"
            f"🌍 Zona horaria: {cal['timezone']}\n"
        )
        
        if cal['description']:
            details_text += f"📝 Descripción: {cal['description']}\n"
            
        if cal['is_primary']:
            details_text += "⭐ Este es tu calendario principal"
        
        self.details_label.config(text=details_text)
        self.select_button.config(state=tk.NORMAL)
        
    def _on_select(self):
        """Confirma selección de calendario"""
        selection = self.calendars_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        cal = self.calendars[index]
        
        # Confirmar
        confirm = messagebox.askyesno(
            "Confirmar selección",
            f"¿Deseas sincronizar las guardias con este calendario?\n\n"
            f"📅 {cal['name']}\n"
            f"🔑 Permisos: {cal['access_role'].upper()}\n\n"
            f"Los eventos se crearán/actualizarán en este calendario.",
            parent=self
        )
        
        if confirm:
            # Guardar configuración
            self.google_sync.set_calendar(
                cal['id'],
                cal['name'],
                cal['access_role']
            )
            
            self.selected_calendar = cal
            
            messagebox.showinfo(
                "Configuración guardada",
                f"✅ Calendario configurado correctamente:\n\n{cal['name']}",
                parent=self
            )
            
            self.destroy()
