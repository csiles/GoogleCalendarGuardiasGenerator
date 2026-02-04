"""
Componente para visualización de múltiples meses en grid
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar as cal


class MultiMonthViewer(tk.Frame):
    """Componente para mostrar vista de múltiples meses"""
    
    def __init__(self, parent, calendar_manager, colors=None, num_months=7, parent_tab=None, **kwargs):
        """
        Inicializa el visor multi-mes.
        
        Args:
            parent: Widget padre
            calendar_manager: Instancia de CalendarManager
            colors: Diccionario de colores por técnico {nombre: #hexcolor}
            num_months: Número de meses a mostrar (default: 7)
            parent_tab: Referencia al tab padre para callbacks
        """
        super().__init__(parent, **kwargs)
        self.calendar_manager = calendar_manager
        self.colors = colors or {}
        self.num_months = num_months
        self.current_offset = 0  # Empezar en el mes actual
        self.parent_tab = parent_tab
        self.dragging_tecnico = None
        
        # Variables para drag-and-drop
        self.dragging = None
        self.drag_label = None
        
        self._create_widgets()
        self.refresh()  # Cargar vista inicial
        
    def _create_widgets(self):
        """Crea los widgets del visor"""
        # Barra de navegación
        nav_frame = tk.Frame(self, bg="#34495e", height=50)
        nav_frame.pack(fill=tk.X, side=tk.TOP)
        nav_frame.pack_propagate(False)
        
        # Frame izquierdo: botones de navegación
        left_nav = tk.Frame(nav_frame, bg="#34495e")
        left_nav.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Botones de navegación
        tk.Button(left_nav, text="◄◄ -1 Año", 
                 command=lambda: self.navigate(-12),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(left_nav, text="◄ -1 Mes", 
                 command=lambda: self.navigate(-1),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(left_nav, text="HOY", 
                 command=self.reset_to_today,
                 bg="#e74c3c", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(left_nav, text="► +1 Mes", 
                 command=lambda: self.navigate(1),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(left_nav, text="►► +1 Año", 
                 command=lambda: self.navigate(12),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Frame derecho: botones de técnicos (si parent_tab existe)
        if self.parent_tab:
            right_nav = tk.Frame(nav_frame, bg="#34495e")
            right_nav.pack(side=tk.RIGHT, padx=10, pady=10)
            
            tk.Label(right_nav, text="👤 Técnicos:", bg="#34495e", fg="white",
                    font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
            
            # Obtener técnicos del parent_tab
            if hasattr(self.parent_tab, 'tecnicos') and hasattr(self.parent_tab, 'colors'):
                for tecnico in self.parent_tab.tecnicos:
                    color = self.parent_tab.colors.get(tecnico, "#3498db")
                    btn = tk.Button(right_nav, text=tecnico, bg=color, fg="white",
                                  font=("Arial", 8, "bold"), relief=tk.RAISED, bd=2,
                                  cursor="hand2", padx=8, pady=2)
                    btn.pack(side=tk.LEFT, padx=2)
                    btn.bind("<Button-1>", lambda e, t=tecnico, c=color: self._start_drag(e, t, c))
        
        # Área de meses con scroll
        scroll_frame = tk.Frame(self, bg="#ecf0f1")
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas con scrollbar
        self.canvas = tk.Canvas(scroll_frame, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ecf0f1")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Habilitar scroll con rueda del ratón
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def navigate(self, months_delta: int):
        """
        Navega meses hacia adelante o atrás.
        
        Args:
            months_delta: Número de meses a mover (+ adelante, - atrás)
        """
        self.current_offset += months_delta
        self.refresh()
        
    def reset_to_today(self):
        """Resetea la vista al mes actual"""
        self.current_offset = 0  # Mes actual
        self.refresh()
        
    def _on_mousewheel(self, event):
        """Maneja el scroll con rueda del ratón"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def set_dragging_tecnico(self, tecnico):
        """Establece el técnico que se está arrastrando"""
        self.dragging_tecnico = tecnico
    
    def _start_drag(self, event, tecnico, color):
        """Inicia arrastre de técnico"""
        self.dragging = {'tecnico': tecnico, 'color': color}
        
        if self.drag_label:
            self.drag_label.destroy()
        
        self.drag_label = tk.Label(self.winfo_toplevel(), text=f"  {tecnico}  ",
                                   font=("Arial", 12, "bold"), bg=color, fg="white",
                                   relief=tk.RAISED, bd=3)
        self.drag_label.place(x=event.x_root - self.winfo_toplevel().winfo_rootx(),
                             y=event.y_root - self.winfo_toplevel().winfo_rooty())
        
        self.winfo_toplevel().bind("<B1-Motion>", self._move_drag)
        self.winfo_toplevel().bind("<ButtonRelease-1>", self._detect_drop)
    
    def _move_drag(self, event):
        """Mueve el label de arrastre"""
        if self.drag_label:
            self.drag_label.place(x=event.x_root - self.winfo_toplevel().winfo_rootx(),
                                 y=event.y_root - self.winfo_toplevel().winfo_rooty())
    
    def _detect_drop(self, event):
        """Detecta dónde se soltó el técnico"""
        if not self.dragging:
            return
        
        if self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None
        self.winfo_toplevel().unbind("<B1-Motion>")
        self.winfo_toplevel().unbind("<ButtonRelease-1>")
        
        widget = self.winfo_toplevel().winfo_containing(event.x_root, event.y_root)
        
        if widget and hasattr(widget, 'fecha_asignada'):
            fecha_obj = widget.fecha_asignada
            fecha = fecha_obj.strftime('%Y-%m-%d')
            
            # Crear evento de guardia
            evento = {
                'id': self.calendar_manager._generate_event_id(fecha, f"Guardia - {self.dragging['tecnico']}"),
                'titulo': f"Guardia - {self.dragging['tecnico']}",
                'tecnico': self.dragging['tecnico'],
                'tipo': 'guardia',
                'descripcion': '',
                'all_day': True,
                'origen': 'manual_edit',
                'fecha_edicion': datetime.now().isoformat()
            }
            
            # Verificar si ya existe un evento y eliminarlo (sobrescribir)
            year_month = fecha[:7]
            day_str = fecha[8:10]
            
            if year_month in self.calendar_manager.data['meses']:
                if day_str in self.calendar_manager.data['meses'][year_month]['dias']:
                    # Limpiar eventos previos del día
                    self.calendar_manager.data['meses'][year_month]['dias'][day_str]['eventos'] = []
            
            # Agregar nuevo evento
            self.calendar_manager.add_event(fecha, evento)
            self.calendar_manager.save_data()
            
            # Actualizar status bar del padre si existe
            if self.parent_tab and hasattr(self.parent_tab, 'status_label'):
                self.parent_tab.status_label.config(
                    text=f"✅ Guardia asignada a {self.dragging['tecnico']} el {fecha}",
                    bg="#2ecc71", fg="white"
                )
            
            self.dragging = None
            # Refrescar vista
            self.refresh()
        else:
            self.dragging = None
    
    def _delete_event(self, event, year, month, day):
        """Elimina un evento al hacer click en él"""
        # Prevenir propagación si estamos arrastrando
        if self.dragging:
            return
        
        fecha = datetime(year, month, day).strftime('%Y-%m-%d')
        year_month = fecha[:7]
        day_str = fecha[8:10]
        
        # Eliminar eventos del día
        if year_month in self.calendar_manager.data['meses']:
            if day_str in self.calendar_manager.data['meses'][year_month]['dias']:
                self.calendar_manager.data['meses'][year_month]['dias'][day_str]['eventos'] = []
                self.calendar_manager.save_data()
                
                # Actualizar status bar
                if self.parent_tab and hasattr(self.parent_tab, 'status_label'):
                    self.parent_tab.status_label.config(
                        text=f"🗑️ Guardia eliminada del {fecha}",
                        bg="#e74c3c", fg="white"
                    )
                
                # Refrescar vista
                self.refresh()
    
    def refresh(self):
        """Refresca la visualización de meses"""
        # Limpiar frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Calcular fecha de inicio
        today = datetime.now()
        start_month = today.month + self.current_offset
        start_year = today.year
        
        # Ajustar año si el mes sale del rango
        while start_month < 1:
            start_month += 12
            start_year -= 1
        while start_month > 12:
            start_month -= 12
            start_year += 1
        
        start_date = datetime(start_year, start_month, 1)
        
        # Obtener datos de múltiples meses
        months_data = self.calendar_manager.get_multi_month_view(start_date, self.num_months)
        
        # Renderizar meses en grid (2 columnas para 7 meses)
        for idx, month_data in enumerate(months_data):
            row = idx // 2
            col = idx % 2
            
            month_frame = self._create_month_frame(month_data)
            month_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Configurar expansión del grid
        for i in range(2):
            self.scrollable_frame.columnconfigure(i, weight=1)
        
    def _create_month_frame(self, month_data: dict) -> tk.Frame:
        """
        Crea frame para un mes individual.
        
        Args:
            month_data: Datos del mes desde CalendarManager
            
        Returns:
            Frame con la visualización del mes
        """
        frame = tk.LabelFrame(self.scrollable_frame, 
                             text=month_data['month_name'],
                             font=("Arial", 11, "bold"),
                             bg="white",
                             relief=tk.RAISED,
                             bd=2)
        
        # Contenedor principal con dos secciones: calendario y estadísticas
        main_container = tk.Frame(frame, bg="white")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Grid de calendario (izquierda)
        cal_grid = tk.Frame(main_container, bg="white")
        cal_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Encabezados de días
        days_headers = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        for col, day_name in enumerate(days_headers):
            bg_color = "#e74c3c" if col >= 5 else "#34495e"
            tk.Label(cal_grid, text=day_name, font=("Arial", 9, "bold"),
                    bg=bg_color, fg="white", width=8).grid(row=0, column=col, sticky="ew", padx=1, pady=1)
        
        # Obtener días del mes
        year = month_data['year']
        month = month_data['month']
        cal_matrix = cal.monthcalendar(year, month)
        
        # Renderizar días
        for week_num, week in enumerate(cal_matrix):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Día vacío
                    tk.Label(cal_grid, text="", bg="#ecf0f1").grid(
                        row=week_num+1, column=day_num, sticky="nsew", padx=1, pady=1)
                else:
                    # Día con posibles eventos
                    day_str = f"{day:02d}"
                    eventos = month_data['dias'].get(day_str, {}).get('eventos', [])
                    
                    # Color de fondo según día
                    bg_color = "#ffe6e6" if day_num >= 5 else "white"
                    
                    day_cell = tk.Frame(cal_grid, bg=bg_color, relief=tk.RIDGE, bd=1, cursor="hand2")
                    day_cell.grid(row=week_num+1, column=day_num, sticky="nsew", padx=1, pady=1)
                    
                    # Asignar fecha al widget para drag-and-drop
                    day_cell.fecha_asignada = datetime(year, month, day)
                    
                    # Número del día
                    day_label = tk.Label(day_cell, text=str(day), font=("Arial", 9, "bold"),
                            bg=bg_color, fg="#2c3e50", cursor="hand2")
                    day_label.pack(anchor="nw", padx=2, pady=2)
                    day_label.fecha_asignada = datetime(year, month, day)
                    
                    # Mostrar eventos
                    if eventos:
                        for evento in eventos[:2]:  # Máximo 2 eventos visibles
                            # Mostrar el nombre del técnico si está disponible, sino el título
                            texto = evento.get('tecnico', evento.get('titulo', 'Evento'))[:15]
                            tecnico = evento.get('tecnico', '')
                            color = self.colors.get(tecnico, "#3498db")
                            event_label = tk.Label(day_cell, text=texto, 
                                    font=("Arial", 7),
                                    bg=color, fg="white",
                                    relief=tk.RAISED, bd=1, cursor="hand2")
                            event_label.pack(fill=tk.X, padx=2, pady=1)
                            event_label.fecha_asignada = datetime(year, month, day)
                            # Bind para borrar guardia con click
                            event_label.bind("<Button-1>", lambda e, y=year, m=month, d=day: self._delete_event(e, y, m, d))
                        
                        if len(eventos) > 2:
                            tk.Label(day_cell, text=f"+{len(eventos)-2} más", 
                                    font=("Arial", 6), fg="gray").pack(pady=1)
        
        # Configurar expansión de columnas
        for i in range(7):
            cal_grid.columnconfigure(i, weight=1, minsize=70)
        
        # Panel de estadísticas (derecha)
        stats_panel = tk.Frame(main_container, bg="#ecf0f1", width=180, relief=tk.SUNKEN, bd=2)
        stats_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        stats_panel.pack_propagate(False)
        
        # Título de estadísticas
        tk.Label(stats_panel, text="Técnicos", font=("Arial", 10, "bold"),
                bg="#34495e", fg="white", pady=5).pack(fill=tk.X)
        
        # Calcular estadísticas por técnico
        counter = {}
        for day_str, day_data in month_data['dias'].items():
            for evento in day_data.get('eventos', []):
                tecnico = evento.get('tecnico', '')
                if tecnico and tecnico not in counter:
                    counter[tecnico] = {'dias': [], 'total': 0}
                
                if tecnico:
                    day_num = int(day_str)
                    counter[tecnico]['dias'].append(day_num)
                    
                    # Detectar si es guardia de TARDE (suma 0.5 en lugar de 1)
                    titulo = evento.get('titulo', '').upper()
                    es_tarde = 'TARDE' in titulo
                    counter[tecnico]['total'] += 0.5 if es_tarde else 1
        
        if counter:
            # Frame con scroll para estadísticas
            stats_frame = tk.Frame(stats_panel, bg="white")
            stats_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Encabezados
            header = tk.Frame(stats_frame, bg="#34495e")
            header.pack(fill=tk.X)
            
            tk.Label(header, text="Técnico", font=("Arial", 8, "bold"),
                    bg="#34495e", fg="white", width=8, anchor="w", padx=3).pack(side=tk.LEFT)
            tk.Label(header, text="Días", font=("Arial", 8, "bold"),
                    bg="#34495e", fg="white", anchor="w", padx=3).pack(side=tk.LEFT, expand=True, fill=tk.X)
            tk.Label(header, text="Tot", font=("Arial", 8, "bold"),
                    bg="#34495e", fg="white", width=4, anchor="center").pack(side=tk.LEFT)
            
            # Filas de técnicos
            for i, (tecnico, info) in enumerate(sorted(counter.items())):
                color = self.colors.get(tecnico, "#3498db")
                row_bg = "#ecf0f1" if i % 2 == 0 else "white"
                
                row = tk.Frame(stats_frame, bg=row_bg)
                row.pack(fill=tk.X)
                
                tk.Label(row, text=tecnico, font=("Arial", 7, "bold"),
                        bg=color, fg="white", width=8, anchor="w", padx=3).pack(side=tk.LEFT)
                
                dias_str = ",".join(map(str, sorted(info['dias'])))
                tk.Label(row, text=dias_str, font=("Arial", 7),
                        bg=row_bg, fg="#2c3e50", anchor="w", padx=3).pack(side=tk.LEFT, expand=True, fill=tk.X)
                
                # Mostrar total (con decimales si es .5)
                total_str = str(info['total']) if info['total'] % 1 != 0 else str(int(info['total']))
                tk.Label(row, text=total_str, font=("Arial", 7, "bold"),
                        bg=row_bg, fg="#2c3e50", width=4, anchor="center").pack(side=tk.LEFT)
        else:
            tk.Label(stats_panel, text="Sin guardias", font=("Arial", 8, "italic"),
                    bg="white", fg="#999", pady=10).pack(fill=tk.BOTH, expand=True)
        
        return frame
