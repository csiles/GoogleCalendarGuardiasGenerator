"""
Componente para visualización de múltiples meses en grid
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar as cal


class MultiMonthViewer(tk.Frame):
    """Componente para mostrar vista de múltiples meses"""
    
    def __init__(self, parent, calendar_manager, num_months=7, **kwargs):
        """
        Inicializa el visor multi-mes.
        
        Args:
            parent: Widget padre
            calendar_manager: Instancia de CalendarManager
            num_months: Número de meses a mostrar (default: 7)
        """
        super().__init__(parent, **kwargs)
        self.calendar_manager = calendar_manager
        self.num_months = num_months
        self.current_offset = -3  # Empezar 3 meses atrás
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Crea los widgets del visor"""
        # Barra de navegación
        nav_frame = tk.Frame(self, bg="#34495e", height=50)
        nav_frame.pack(fill=tk.X, side=tk.TOP)
        nav_frame.pack_propagate(False)
        
        # Botones de navegación
        tk.Button(nav_frame, text="◄◄ -1 Año", 
                 command=lambda: self.navigate(-12),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(nav_frame, text="◄ -1 Mes", 
                 command=lambda: self.navigate(-1),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(nav_frame, text="HOY", 
                 command=self.reset_to_today,
                 bg="#e74c3c", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=10)
        
        tk.Button(nav_frame, text="► +1 Mes", 
                 command=lambda: self.navigate(1),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(nav_frame, text="►► +1 Año", 
                 command=lambda: self.navigate(12),
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
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
        self.current_offset = -3  # 3 meses atrás del actual
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
        
        # Grid de calendario
        cal_grid = tk.Frame(frame, bg="white")
        cal_grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
                    
                    day_cell = tk.Frame(cal_grid, bg=bg_color, relief=tk.RIDGE, bd=1)
                    day_cell.grid(row=week_num+1, column=day_num, sticky="nsew", padx=1, pady=1)
                    
                    # Número del día
                    tk.Label(day_cell, text=str(day), font=("Arial", 9, "bold"),
                            bg=bg_color, fg="#2c3e50").pack(anchor="nw", padx=2, pady=2)
                    
                    # Mostrar eventos
                    if eventos:
                        for evento in eventos[:2]:  # Máximo 2 eventos visibles
                            tk.Label(day_cell, text=evento['titulo'][:15], 
                                    font=("Arial", 7),
                                    bg="#3498db", fg="white",
                                    relief=tk.RAISED, bd=1).pack(fill=tk.X, padx=2, pady=1)
                        
                        if len(eventos) > 2:
                            tk.Label(day_cell, text=f"+{len(eventos)-2} más", 
                                    font=("Arial", 6), fg="gray").pack(pady=1)
        
        # Configurar expansión de columnas
        for i in range(7):
            cal_grid.columnconfigure(i, weight=1, minsize=80)
        
        # Estadísticas del mes
        total_eventos = month_data.get('estadisticas_mes', {}).get('total_eventos', 0)
        if total_eventos > 0:
            stats_label = tk.Label(frame, text=f"📊 {total_eventos} eventos",
                                  font=("Arial", 8), bg="white", fg="gray")
            stats_label.pack(pady=5)
        
        return frame
