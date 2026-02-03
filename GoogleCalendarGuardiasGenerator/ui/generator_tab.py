"""
Pestaña de generación de guardias con drag-and-drop
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import csv
from typing import Dict, List
from utils.file_utils import load_tecnicos, load_festivos, get_technician_colors


class GeneratorTab(tk.Frame):
    """Pestaña para generar y asignar guardias"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Cargar datos
        self.tecnicos = load_tecnicos()
        self.festivos = load_festivos()
        self.colors = get_technician_colors()
        
        # Estado de la aplicación
        self.asignaciones = {}  # {fecha: {'tecnico': str, 'color': str}}
        self.dragging = None
        self.drag_label = None
        self.year = 2026
        self.month = 3  # Marzo
        
        self._create_widgets()
        self._draw_calendar()
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        self._create_header()
        self._create_control_panel()
        self._create_calendar_area()
        self._create_stats_panel()
    
    def _create_header(self):
        """Crea el encabezado de la pestaña"""
        header = tk.Frame(self, bg="#2c3e50", height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="📅 Generador de Guardias - Soporte", 
                font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(pady=10)
    
    def _create_control_panel(self):
        """Crea el panel de controles (técnico anterior, período, técnicos)"""
        panel = tk.Frame(self, bg="#ecf0f1", height=100)
        panel.pack(fill=tk.X, padx=10, pady=10)
        panel.pack_propagate(False)
        
        # Bloque 1: Último técnico
        self._create_last_tech_selector(panel)
        
        # Bloque 2: Período de fechas
        self._create_date_range_selector(panel)
        
        # Bloque 3: Técnicos arrastrables
        self._create_technicians_grid(panel)
    
    def _create_last_tech_selector(self, parent):
        """Crea selector de último técnico"""
        block = tk.LabelFrame(parent, text="Último técnico", 
                             font=("Arial", 8, "bold"), bg="#ecf0f1", 
                             relief=tk.RIDGE, bd=2)
        block.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH)
        block.pack_propagate(False)
        block.config(width=180)
        
        self.ultimo_tecnico_var = tk.StringVar(value=self.tecnicos[0] if self.tecnicos else "")
        ttk.Combobox(block, textvariable=self.ultimo_tecnico_var,
                    values=self.tecnicos, state="readonly",
                    font=("Arial", 9), width=12).pack(padx=5, pady=5)
    
    def _create_date_range_selector(self, parent):
        """Crea selector de rango de fechas"""
        block = tk.LabelFrame(parent, text="Período",
                             font=("Arial", 8, "bold"), bg="#ecf0f1",
                             relief=tk.RIDGE, bd=2)
        block.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH)
        block.pack_propagate(False)
        block.config(width=180)
        
        frame = tk.Frame(block, bg="#ecf0f1")
        frame.pack(padx=5, pady=5)
        
        # Fecha inicio
        tk.Label(frame, text="Inicio:", font=("Arial", 8), 
                bg="#ecf0f1").grid(row=0, column=0, sticky="w", padx=2, pady=1)
        self.fecha_inicio_var = tk.StringVar(value="01/01/2026")
        tk.Entry(frame, textvariable=self.fecha_inicio_var,
                font=("Arial", 8), width=10).grid(row=0, column=1, padx=2, pady=1)
        
        # Fecha fin
        tk.Label(frame, text="Fin:", font=("Arial", 8), 
                bg="#ecf0f1").grid(row=1, column=0, sticky="w", padx=2, pady=1)
        self.fecha_fin_var = tk.StringVar(value="31/12/2026")
        tk.Entry(frame, textvariable=self.fecha_fin_var,
                font=("Arial", 8), width=10).grid(row=1, column=1, padx=2, pady=1)
    
    def _create_technicians_grid(self, parent):
        """Crea grid de técnicos arrastrables"""
        block = tk.LabelFrame(parent, text="Técnicos (arrastra al calendario)",
                             font=("Arial", 8, "bold"), bg="#ecf0f1",
                             relief=tk.RIDGE, bd=2)
        block.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        grid = tk.Frame(block, bg="#ecf0f1")
        grid.pack(padx=5, pady=5, expand=True)
        
        colores = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        
        # Grid 1 fila x 6 columnas
        for i, tecnico in enumerate(self.tecnicos):
            color = colores[i % len(colores)]
            btn = tk.Label(grid, text=tecnico, font=("Arial", 9, "bold"),
                          bg=color, fg="white", relief=tk.RAISED, bd=2,
                          cursor="hand2", padx=10, pady=5, width=10)
            btn.grid(row=0, column=i, padx=3, pady=3, sticky="ew")
            btn.bind("<Button-1>", lambda e, t=tecnico, c=color: self._start_drag(e, t, c))
        
        for i in range(6):
            grid.columnconfigure(i, weight=1)
    
    def _create_calendar_area(self):
        """Crea el área del calendario con navegación"""
        # Contenedor principal
        main_container = tk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Frame del calendario (izquierda, 80%)
        cal_frame = tk.Frame(main_container)
        cal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Navegación del mes
        nav = tk.Frame(cal_frame, bg="#34495e", height=50)
        nav.pack(fill=tk.X)
        nav.pack_propagate(False)
        
        tk.Button(nav, text="◀", command=self._prev_month,
                 font=("Arial", 14, "bold"), bg="#2c3e50", fg="white",
                 relief=tk.FLAT, cursor="hand2", width=3).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.month_label = tk.Label(nav, text="", font=("Arial", 16, "bold"),
                                   bg="#34495e", fg="white")
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        tk.Button(nav, text="▶", command=self._next_month,
                 font=("Arial", 14, "bold"), bg="#2c3e50", fg="white",
                 relief=tk.FLAT, cursor="hand2", width=3).pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Grid del calendario
        self.calendar_frame = tk.Frame(cal_frame, bg="white")
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel derecho (guardamos referencia para crearlo después)
        self.stats_container = tk.Frame(main_container, bg="#ecf0f1", width=250, 
                                       relief=tk.RIDGE, bd=2)
        self.stats_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
        self.stats_container.pack_propagate(False)
    
    def _create_stats_panel(self):
        """Crea el panel de estadísticas y botones de acción"""
        # Contador de guardias
        counter_frame = tk.LabelFrame(self.stats_container, text="📊 Guardias del mes", 
                                     font=("Arial", 10, "bold"), bg="#ecf0f1",
                                     relief=tk.RIDGE, bd=2)
        counter_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Canvas con scroll
        canvas = tk.Canvas(counter_frame, bg="white")
        scrollbar = ttk.Scrollbar(counter_frame, orient="vertical", command=canvas.yview)
        self.stats_frame = tk.Frame(canvas, bg="white")
        
        self.stats_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.stats_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones de acción
        actions = tk.Frame(self.stats_container, bg="#ecf0f1")
        actions.pack(side=tk.BOTTOM, pady=10, padx=10, fill=tk.X)
        
        tk.Button(actions, text="🔄 Auto-asignar", command=self._auto_assign,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", pady=6).pack(fill=tk.X, pady=3)
        
        tk.Button(actions, text="🗑️ Limpiar", command=self._clear_assignments,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", pady=6).pack(fill=tk.X, pady=3)
        
        tk.Button(actions, text="💾 Exportar CSV", command=self._export_csv,
                 bg="#2ecc71", fg="white", font=("Arial", 11, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", pady=8).pack(fill=tk.X, pady=3)
    
    def _draw_calendar(self):
        """Dibuja el calendario del mes actual"""
        # Limpiar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Actualizar título
        months = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_label.config(text=f"{months[self.month]} {self.year}")
        
        # Encabezados
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, day in enumerate(days):
            color = "#e74c3c" if i >= 5 else "#34495e"
            tk.Label(self.calendar_frame, text=day, font=("Arial", 10, "bold"),
                    bg=color, fg="white", relief=tk.RIDGE, bd=1, pady=3).grid(
                    row=0, column=i, sticky="nsew", padx=1, pady=1)
        
        # Días
        cal = calendar.monthcalendar(self.year, self.month)
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    tk.Label(self.calendar_frame, text="", bg="#ecf0f1",
                            relief=tk.FLAT).grid(row=week_num+1, column=day_num,
                            sticky="nsew", padx=1, pady=1)
                else:
                    fecha = datetime(self.year, self.month, day).date()
                    self._create_day_cell(week_num+1, day_num, day, fecha)
        
        # Configurar grid
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1, minsize=120)
        self.calendar_frame.rowconfigure(0, weight=0, minsize=30)
        for i in range(1, len(cal) + 1):
            self.calendar_frame.rowconfigure(i, weight=1, minsize=80)
        
        # Actualizar estadísticas
        self._update_stats()
    
    def _create_day_cell(self, row: int, col: int, day: int, fecha: datetime):
        """Crea una celda de día en el calendario"""
        is_weekend = col >= 5
        is_holiday = fecha in self.festivos
        weekday = fecha.weekday()
        
        # Color de fondo
        bg_color = "#ffe6e6" if is_weekend else ("#fff3cd" if is_holiday else "white")
        
        # Frame del día
        frame = tk.Frame(self.calendar_frame, bg=bg_color, relief=tk.RIDGE, bd=2)
        
        # Encabezado
        header = tk.Frame(frame, bg=bg_color)
        header.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(header, text=str(day), font=("Arial", 11, "bold"),
                bg=bg_color, fg="#2c3e50").pack(side=tk.LEFT)
        
        if is_holiday:
            festivo_text = self.festivos[fecha] if self.festivos[fecha] else "Festivo"
            tk.Label(header, text=f"🎉{festivo_text}", font=("Arial", 7),
                    bg=bg_color, fg="#856404").pack(side=tk.RIGHT)
        
        # Zona de asignación (solo fines de semana y festivos laborables)
        if is_weekend or (is_holiday and weekday < 5):
            drop_frame = tk.Frame(frame, bg=bg_color, relief=tk.SUNKEN, bd=1)
            drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            drop_frame.fecha_asignada = fecha
            frame.fecha_asignada = fecha
            
            if fecha in self.asignaciones:
                tecnico = self.asignaciones[fecha]['tecnico']
                color = self.asignaciones[fecha]['color']
                lbl = tk.Label(drop_frame, text=tecnico, font=("Arial", 10, "bold"),
                              bg=color, fg="white", relief=tk.RAISED, bd=2, pady=5)
                lbl.pack(fill=tk.BOTH, expand=True)
                lbl.bind("<Double-Button-1>", lambda e, f=fecha: self._remove_assignment(f))
                lbl.fecha_asignada = fecha
            else:
                placeholder = tk.Label(drop_frame, text="Arrastra\naquí",
                                      font=("Arial", 9), bg=bg_color, fg="#999")
                placeholder.pack(fill=tk.BOTH, expand=True)
                placeholder.fecha_asignada = fecha
            
            drop_frame.bind("<ButtonRelease-1>", lambda e, f=fecha: self._drop_technician(e, f))
            frame.bind("<ButtonRelease-1>", lambda e, f=fecha: self._drop_technician(e, f))
        
        frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
    
    def _start_drag(self, event, tecnico: str, color: str):
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
            fecha = widget.fecha_asignada
            
            if fecha.weekday() >= 5 and fecha in self.festivos:
                if not messagebox.askyesno("Confirmar",
                    f"Este festivo cae en fin de semana.\n¿Asignar guardia de fin de semana a {self.dragging['tecnico']}?"):
                    self.dragging = None
                    return
            
            self.asignaciones[fecha] = {
                'tecnico': self.dragging['tecnico'],
                'color': self.dragging['color']
            }
            self.dragging = None
            self._draw_calendar()
        else:
            self.dragging = None
    
    def _drop_technician(self, event, fecha: datetime):
        """Asigna técnico a una fecha"""
        if self.dragging:
            if fecha.weekday() >= 5 and fecha in self.festivos:
                if not messagebox.askyesno("Confirmar",
                    f"Este festivo cae en fin de semana.\n¿Asignar guardia de fin de semana a {self.dragging['tecnico']}?"):
                    return
            
            self.asignaciones[fecha] = {
                'tecnico': self.dragging['tecnico'],
                'color': self.dragging['color']
            }
            self._draw_calendar()
    
    def _remove_assignment(self, fecha: datetime):
        """Quita asignación de una fecha"""
        if fecha in self.asignaciones:
            del self.asignaciones[fecha]
            self._draw_calendar()
    
    def _update_stats(self):
        """Actualiza estadísticas de guardias del mes"""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Contar guardias
        counter = {}
        for fecha, datos in self.asignaciones.items():
            if fecha.year == self.year and fecha.month == self.month:
                tecnico = datos['tecnico']
                if tecnico not in counter:
                    counter[tecnico] = {'dias': [], 'total': 0}
                
                es_tarde = fecha in self.festivos and "TARDE" in self.festivos[fecha].upper()
                counter[tecnico]['dias'].append(fecha.day)
                counter[tecnico]['total'] += 0.5 if es_tarde else 1
        
        if not counter:
            tk.Label(self.stats_frame, text="Sin guardias este mes",
                    font=("Arial", 9, "italic"), fg="#999", bg="white").pack(pady=20)
            return
        
        # Encabezados
        header = tk.Frame(self.stats_frame, bg="#34495e")
        header.pack(fill=tk.X, padx=2, pady=2)
        
        tk.Label(header, text="Técnico", font=("Arial", 9, "bold"),
                bg="#34495e", fg="white", width=10, anchor="w", padx=5).pack(side=tk.LEFT)
        tk.Label(header, text="Días", font=("Arial", 9, "bold"),
                bg="#34495e", fg="white", width=8, anchor="w", padx=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(header, text="Total", font=("Arial", 9, "bold"),
                bg="#34495e", fg="white", width=5, anchor="center").pack(side=tk.LEFT)
        
        # Filas
        colores = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        for i, (tecnico, info) in enumerate(sorted(counter.items())):
            idx = self.tecnicos.index(tecnico) if tecnico in self.tecnicos else 0
            color = colores[idx % len(colores)]
            
            row_bg = "#ecf0f1" if i % 2 == 0 else "white"
            row = tk.Frame(self.stats_frame, bg=row_bg, relief=tk.FLAT, bd=1)
            row.pack(fill=tk.X, padx=2, pady=1)
            
            tk.Label(row, text=tecnico, font=("Arial", 9, "bold"),
                    bg=color, fg="white", width=10, anchor="w", padx=5).pack(side=tk.LEFT)
            
            dias_str = ",".join(map(str, sorted(info['dias'])))
            tk.Label(row, text=dias_str, font=("Arial", 9),
                    bg=row_bg, fg="#2c3e50", anchor="w", padx=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            total_str = str(info['total']) if info['total'] % 1 != 0 else str(int(info['total']))
            tk.Label(row, text=total_str, font=("Arial", 9, "bold"),
                    bg=row_bg, fg="#2c3e50", width=5, anchor="center").pack(side=tk.LEFT)
    
    def _prev_month(self):
        """Navega al mes anterior"""
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._draw_calendar()
    
    def _next_month(self):
        """Navega al mes siguiente"""
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._draw_calendar()
    
    def _clear_assignments(self):
        """Limpia todas las asignaciones"""
        if messagebox.askyesno("Confirmar", "¿Borrar todas las asignaciones?"):
            self.asignaciones = {}
            self._draw_calendar()
    
    def _auto_assign(self):
        """Auto-asigna técnicos automáticamente"""
        if not messagebox.askyesno("Auto-asignar",
            "Esto asignará automáticamente técnicos siguiendo las reglas:\n" +
            "- No se asigna el mismo técnico a bloques separados consecutivos\n" +
            "- Bloques de 3 días: mismo técnico\n" +
            "- Bloques de 4+ días: se dividen en sub-bloques de 2 días\n\n¿Continuar?"):
            return
        
        try:
            fecha_inicio = datetime.strptime(self.fecha_inicio_var.get(), "%d/%m/%Y").date()
            fecha_fin = datetime.strptime(self.fecha_fin_var.get(), "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido.\nUse DD/MM/AAAA")
            return
        
        if fecha_fin < fecha_inicio:
            messagebox.showerror("Error", "La fecha de fin debe ser posterior a la fecha de inicio")
            return
        
        self.asignaciones = {}
        
        # Identificar días de guardia
        dias_guardia = set()
        fecha = fecha_inicio
        while fecha <= fecha_fin:
            if fecha.weekday() in [5, 6]:
                dias_guardia.add(fecha)
            fecha += timedelta(days=1)
        
        for fecha_festivo in self.festivos.keys():
            if fecha_inicio <= fecha_festivo <= fecha_fin and fecha_festivo.weekday() < 5:
                dias_guardia.add(fecha_festivo)
        
        # Agrupar en bloques consecutivos
        dias_ordenados = sorted(dias_guardia)
        bloques = []
        bloque_actual = []
        
        for dia in dias_ordenados:
            if not bloque_actual:
                bloque_actual = [dia]
            else:
                if (dia - bloque_actual[-1]).days == 1:
                    bloque_actual.append(dia)
                else:
                    bloques.append(bloque_actual)
                    bloque_actual = [dia]
        
        if bloque_actual:
            bloques.append(bloque_actual)
        
        # Asignar técnicos
        ultimo_tecnico = self.ultimo_tecnico_var.get()
        if ultimo_tecnico in self.tecnicos:
            indice_tecnico = (self.tecnicos.index(ultimo_tecnico) + 1) % len(self.tecnicos)
        else:
            indice_tecnico = 0
        
        ultimo_tecnico_asignado = None
        colores = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        
        for bloque in bloques:
            num_dias = len(bloque)
            
            tecnico_inicial = indice_tecnico
            if ultimo_tecnico_asignado is not None:
                while self.tecnicos[indice_tecnico] == ultimo_tecnico_asignado:
                    indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
                    if indice_tecnico == tecnico_inicial:
                        break
            
            if num_dias <= 2:
                tecnico = self.tecnicos[indice_tecnico]
                color = colores[indice_tecnico % 6]
                for dia in bloque:
                    self.asignaciones[dia] = {'tecnico': tecnico, 'color': color}
                ultimo_tecnico_asignado = tecnico
                indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
            
            elif num_dias == 3:
                tecnico = self.tecnicos[indice_tecnico]
                color = colores[indice_tecnico % 6]
                for dia in bloque:
                    self.asignaciones[dia] = {'tecnico': tecnico, 'color': color}
                ultimo_tecnico_asignado = tecnico
                indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
            
            else:
                i = 0
                while i < num_dias:
                    if i > 0:
                        indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
                    
                    tecnico = self.tecnicos[indice_tecnico]
                    color = colores[indice_tecnico % 6]
                    
                    dias_asignar = min(2, num_dias - i)
                    for j in range(dias_asignar):
                        self.asignaciones[bloque[i + j]] = {'tecnico': tecnico, 'color': color}
                    
                    ultimo_tecnico_asignado = tecnico
                    i += dias_asignar
        
        self._draw_calendar()
        messagebox.showinfo("Completado",
            f"✅ Asignación automática completada\n\n" +
            f"Bloques procesados: {len(bloques)}\n" +
            f"Días asignados: {len(self.asignaciones)}")
    
    def _export_csv(self):
        """Exporta asignaciones a CSV"""
        if not self.asignaciones:
            messagebox.showwarning("Advertencia", "No hay asignaciones para exportar")
            return
        
        asignaciones_ordenadas = sorted(self.asignaciones.items(), key=lambda x: x[0])
        
        eventos = []
        i = 0
        while i < len(asignaciones_ordenadas):
            fecha, datos = asignaciones_ordenadas[i]
            tecnico = datos['tecnico']
            
            if fecha.weekday() == 5:
                fecha_domingo = fecha + timedelta(days=1)
                if i + 1 < len(asignaciones_ordenadas):
                    siguiente_fecha, siguiente_datos = asignaciones_ordenadas[i + 1]
                    if siguiente_fecha == fecha_domingo and siguiente_datos['tecnico'] == tecnico:
                        eventos.append({
                            'fecha_inicio': fecha,
                            'fecha_fin': fecha_domingo,
                            'tecnico': tecnico,
                            'subject': f"Guardia - {tecnico}"
                        })
                        i += 2
                        continue
            
            anotacion = self.festivos.get(fecha, "")
            subject = f"Guardia {anotacion} - {tecnico}" if anotacion else f"Guardia - {tecnico}"
            
            eventos.append({
                'fecha_inicio': fecha,
                'fecha_fin': fecha,
                'tecnico': tecnico,
                'subject': subject
            })
            i += 1
        
        nombre_archivo = "guardias-support.csv"
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',')
            writer.writerow([
                "Subject", "Start Date", "Start Time", "End Date", "End Time",
                "All Day Event", "Description", "Location", "Private"
            ])
            
            for evento in eventos:
                writer.writerow([
                    evento['subject'],
                    evento['fecha_inicio'].strftime("%d/%m/%Y"),
                    "",
                    evento['fecha_fin'].strftime("%d/%m/%Y"),
                    "",
                    "True",
                    "",
                    "",
                    "False"
                ])
        
        messagebox.showinfo("Éxito",
            f"✅ CSV exportado correctamente\n\nArchivo: {nombre_archivo}\nEventos: {len(eventos)}")
