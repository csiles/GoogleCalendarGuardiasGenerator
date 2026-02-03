import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import calendar
import csv
import os

class GuardiasGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Guardias - Soporte")
        self.root.geometry("1400x850")
        
        # Cargar técnicos y festivos
        self.tecnicos = self.leer_tecnicos()
        self.festivos = self.leer_festivos()
        
        # Diccionario para guardar asignaciones: {fecha: tecnico}
        self.asignaciones = {}
        
        # Variables de drag and drop
        self.dragging = None
        self.drag_label = None
        
        # Año y mes actual
        self.year = 2026
        self.month = 3  # Marzo
        
        self.crear_interfaz()
        self.dibujar_calendario()
    
    def leer_tecnicos(self):
        """Lee la lista de técnicos desde tecnicos.txt"""
        try:
            with open("tecnicos.txt", 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return ["Pilar", "Isa", "Romane", "Yannick", "Mayra", "Alberto"]
    
    def leer_festivos(self):
        """Lee la lista de festivos desde festivos.txt"""
        festivos = {}
        try:
            with open("festivos.txt", 'r', encoding='utf-8') as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea:
                        continue
                    partes = linea.split(',', 1)
                    fecha_str = partes[0].strip()
                    anotacion = partes[1].strip() if len(partes) > 1 else ""
                    try:
                        fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                        festivos[fecha] = anotacion
                    except:
                        pass
        except:
            pass
        return festivos
    
    def crear_interfaz(self):
        # Frame superior con controles
        top_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.pack_propagate(False)
        
        # Título
        title = tk.Label(top_frame, text="📅 Generador de Guardias - Soporte", 
                        font=("Arial", 14, "bold"), bg="#2c3e50", fg="white")
        title.pack(pady=10)
        
        # ============ PRIMERA FILA: 3 BLOQUES HORIZONTALES ============
        primera_fila = tk.Frame(self.root, bg="#ecf0f1", height=100)
        primera_fila.pack(fill=tk.X, padx=10, pady=10)
        primera_fila.pack_propagate(False)
        
        # BLOQUE 1: Selector de último técnico (izquierda) - 20%
        bloque1 = tk.LabelFrame(primera_fila, text="Último técnico", 
                                font=("Arial", 8, "bold"), bg="#ecf0f1", relief=tk.RIDGE, bd=2)
        bloque1.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH)
        bloque1.pack_propagate(False)
        bloque1.config(width=180)
        
        self.ultimo_tecnico_var = tk.StringVar(value=self.tecnicos[0] if self.tecnicos else "")
        self.combo_ultimo_tecnico = ttk.Combobox(bloque1, 
                                                  textvariable=self.ultimo_tecnico_var,
                                                  values=self.tecnicos,
                                                  state="readonly",
                                                  font=("Arial", 9),
                                                  width=12)
        self.combo_ultimo_tecnico.pack(padx=5, pady=5)
        
        # BLOQUE 2: Período de fechas (centro) - 20%
        bloque2 = tk.LabelFrame(primera_fila, text="Período",
                                font=("Arial", 8, "bold"), bg="#ecf0f1", relief=tk.RIDGE, bd=2)
        bloque2.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH)
        bloque2.pack_propagate(False)
        bloque2.config(width=180)
        
        fechas_frame = tk.Frame(bloque2, bg="#ecf0f1")
        fechas_frame.pack(padx=5, pady=5)
        
        # Fecha inicio
        tk.Label(fechas_frame, text="Inicio:", font=("Arial", 8), 
                bg="#ecf0f1").grid(row=0, column=0, sticky="w", padx=2, pady=1)
        self.fecha_inicio_var = tk.StringVar(value="01/01/2026")
        tk.Entry(fechas_frame, textvariable=self.fecha_inicio_var,
                font=("Arial", 8), width=10).grid(row=0, column=1, padx=2, pady=1)
        
        # Fecha fin
        tk.Label(fechas_frame, text="Fin:", font=("Arial", 8), 
                bg="#ecf0f1").grid(row=1, column=0, sticky="w", padx=2, pady=1)
        self.fecha_fin_var = tk.StringVar(value="31/12/2026")
        tk.Entry(fechas_frame, textvariable=self.fecha_fin_var,
                font=("Arial", 8), width=10).grid(row=1, column=1, padx=2, pady=1)
        
        # BLOQUE 3: Botones de técnicos (derecha) - Expandible
        bloque3 = tk.LabelFrame(primera_fila, text="Técnicos (arrastra al calendario)",
                                font=("Arial", 8, "bold"), bg="#ecf0f1", relief=tk.RIDGE, bd=2)
        bloque3.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        tecnicos_grid = tk.Frame(bloque3, bg="#ecf0f1")
        tecnicos_grid.pack(padx=5, pady=5, expand=True)
        
        colores_tecnicos = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        
        # Grid 1 fila x 6 columnas
        for i, tecnico in enumerate(self.tecnicos):
            color = colores_tecnicos[i % len(colores_tecnicos)]
            btn = tk.Label(tecnicos_grid, text=tecnico, 
                          font=("Arial", 9, "bold"), bg=color, fg="white",
                          relief=tk.RAISED, bd=2, cursor="hand2", padx=10, pady=5, width=10)
            btn.grid(row=0, column=i, padx=3, pady=3, sticky="ew")
            btn.bind("<Button-1>", lambda e, t=tecnico, c=color: self.iniciar_drag(e, t, c))
        
        # Configurar columnas del grid
        for i in range(6):
            tecnicos_grid.columnconfigure(i, weight=1)
        
        # ============ SEGUNDA FILA: CALENDARIO (80%) + PANEL DERECHO (20%) ============
        segunda_fila = tk.Frame(self.root)
        segunda_fila.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # CALENDARIO (80% - izquierda)
        calendario_frame = tk.Frame(segunda_fila)
        calendario_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Controles de navegación del calendario
        nav_frame = tk.Frame(calendario_frame, bg="#34495e", height=50)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)
        
        tk.Button(nav_frame, text="◀", command=self.mes_anterior,
                 font=("Arial", 14, "bold"), bg="#2c3e50", fg="white",
                 relief=tk.FLAT, cursor="hand2", width=3).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.mes_label = tk.Label(nav_frame, text="", font=("Arial", 16, "bold"),
                                  bg="#34495e", fg="white")
        self.mes_label.pack(side=tk.LEFT, expand=True)
        
        tk.Button(nav_frame, text="▶", command=self.mes_siguiente,
                 font=("Arial", 14, "bold"), bg="#2c3e50", fg="white",
                 relief=tk.FLAT, cursor="hand2", width=3).pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Canvas para el calendario
        self.calendar_frame = tk.Frame(calendario_frame, bg="white")
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # PANEL DERECHO (20%)
        panel_derecho = tk.Frame(segunda_fila, bg="#ecf0f1", width=250, relief=tk.RIDGE, bd=2)
        panel_derecho.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
        panel_derecho.pack_propagate(False)
        
        # Contador de guardias del mes
        contador_frame = tk.LabelFrame(panel_derecho, text="📊 Guardias del mes", 
                                       font=("Arial", 10, "bold"), bg="#ecf0f1",
                                       relief=tk.RIDGE, bd=2)
        contador_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Frame con scroll para la tabla
        canvas_contador = tk.Canvas(contador_frame, bg="white")
        scrollbar = ttk.Scrollbar(contador_frame, orient="vertical", command=canvas_contador.yview)
        self.tabla_contador_frame = tk.Frame(canvas_contador, bg="white")
        
        self.tabla_contador_frame.bind(
            "<Configure>",
            lambda e: canvas_contador.configure(scrollregion=canvas_contador.bbox("all"))
        )
        
        canvas_contador.create_window((0, 0), window=self.tabla_contador_frame, anchor="nw")
        canvas_contador.configure(yscrollcommand=scrollbar.set)
        
        canvas_contador.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones de acción
        action_frame = tk.Frame(panel_derecho, bg="#ecf0f1")
        action_frame.pack(side=tk.BOTTOM, pady=10, padx=10, fill=tk.X)
        
        tk.Button(action_frame, text="🔄 Auto-asignar", command=self.auto_asignar,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"), 
                 relief=tk.RAISED, bd=3, cursor="hand2", pady=6).pack(fill=tk.X, pady=3)
        
        tk.Button(action_frame, text="🗑️ Limpiar", command=self.limpiar_asignaciones,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", pady=6).pack(fill=tk.X, pady=3)
        
        tk.Button(action_frame, text="💾 Exportar CSV", command=self.exportar_csv,
                 bg="#2ecc71", fg="white", font=("Arial", 11, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", pady=8).pack(fill=tk.X, pady=3)
    
    def dibujar_calendario(self):
        # Limpiar calendario anterior
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Actualizar título del mes
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.mes_label.config(text=f"{meses[self.month]} {self.year}")
        
        # Crear grid del calendario
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        
        # Encabezados de días
        for i, dia in enumerate(dias_semana):
            color = "#e74c3c" if i >= 5 else "#34495e"  # Rojo para fin de semana
            tk.Label(self.calendar_frame, text=dia, font=("Arial", 10, "bold"),
                    bg=color, fg="white", relief=tk.RIDGE, bd=1, pady=3).grid(
                    row=0, column=i, sticky="nsew", padx=1, pady=1)
        
        # Obtener días del mes
        cal = calendar.monthcalendar(self.year, self.month)
        
        # Dibujar días
        for semana_num, semana in enumerate(cal):
            for dia_num, dia in enumerate(semana):
                if dia == 0:
                    # Día vacío
                    tk.Label(self.calendar_frame, text="", bg="#ecf0f1",
                            relief=tk.FLAT).grid(row=semana_num+1, column=dia_num,
                            sticky="nsew", padx=1, pady=1)
                else:
                    fecha = datetime(self.year, self.month, dia).date()
                    self.crear_celda_dia(semana_num+1, dia_num, dia, fecha)
        
        # Configurar expansión de grid con tamaño mínimo uniforme
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1, minsize=120)
        # Fila 0 (encabezados) con altura mínima
        self.calendar_frame.rowconfigure(0, weight=0, minsize=30)
        # Resto de filas (días) con altura reducida
        for i in range(1, len(cal) + 1):
            self.calendar_frame.rowconfigure(i, weight=1, minsize=80)
        
        # Actualizar contador de guardias
        self.actualizar_contador_guardias()
    
    def crear_celda_dia(self, row, col, dia, fecha):
        es_fin_semana = col >= 5  # Sábado o Domingo
        es_festivo = fecha in self.festivos
        dia_semana = fecha.weekday()
        
        # Color de fondo
        if es_fin_semana:
            bg_color = "#ffe6e6"
        elif es_festivo:
            bg_color = "#fff3cd"
        else:
            bg_color = "white"
        
        # Frame para el día
        frame = tk.Frame(self.calendar_frame, bg=bg_color, relief=tk.RIDGE, bd=2)
        # Encabezado del día: número + etiqueta festivo en misma línea
        header_frame = tk.Frame(frame, bg=bg_color)
        header_frame.pack(fill=tk.X, padx=3, pady=2)
        
        # Número del día (izquierda)
        dia_label = tk.Label(header_frame, text=str(dia), font=("Arial", 11, "bold"),
                            bg=bg_color, fg="#2c3e50")
        dia_label.pack(side=tk.LEFT)
        
        # Etiqueta de festivo (derecha, en la misma línea)
        if es_festivo:
            festivo_text = self.festivos[fecha] if self.festivos[fecha] else "Festivo"
            tk.Label(header_frame, text=f"🎉{festivo_text}", font=("Arial", 7),
                    bg=bg_color, fg="#856404").pack(side=tk.RIGHT)
        
        # Zona de asignación (solo fines de semana y festivos laborables)
        if es_fin_semana or (es_festivo and dia_semana < 5):
            drop_frame = tk.Frame(frame, bg=bg_color, relief=tk.SUNKEN, bd=1)
            drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Marcar el frame con la fecha para el drag and drop
            drop_frame.fecha_asignada = fecha
            frame.fecha_asignada = fecha
            
            # Label para mostrar técnico asignado
            if fecha in self.asignaciones:
                tecnico = self.asignaciones[fecha]['tecnico']
                color = self.asignaciones[fecha]['color']
                asig_label = tk.Label(drop_frame, text=tecnico, font=("Arial", 10, "bold"),
                                     bg=color, fg="white", relief=tk.RAISED, bd=2, pady=5)
                asig_label.pack(fill=tk.BOTH, expand=True)
                asig_label.bind("<Double-Button-1>", lambda e, f=fecha: self.quitar_asignacion(f))
                asig_label.fecha_asignada = fecha
            else:
                placeholder = tk.Label(drop_frame, text="Arrastra\naquí", 
                                      font=("Arial", 9), bg=bg_color, fg="#999")
                placeholder.pack(fill=tk.BOTH, expand=True)
                placeholder.fecha_asignada = fecha
            
            # Eventos de drop
            drop_frame.bind("<ButtonRelease-1>", lambda e, f=fecha: self.soltar_tecnico(e, f))
            frame.bind("<ButtonRelease-1>", lambda e, f=fecha: self.soltar_tecnico(e, f))
        
        # Colocar el frame en el grid
        frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
    
    def iniciar_drag(self, event, tecnico, color):
        """Inicia el drag de un técnico"""
        self.dragging = {'tecnico': tecnico, 'color': color}
        
        # Crear label flotante
        if self.drag_label:
            self.drag_label.destroy()
        
        self.drag_label = tk.Label(self.root, text=f"  {tecnico}  ", 
                                   font=("Arial", 12, "bold"), bg=color, fg="white",
                                   relief=tk.RAISED, bd=3)
        self.drag_label.place(x=event.x_root - self.root.winfo_rootx(), 
                             y=event.y_root - self.root.winfo_rooty())
        
        # Bind para seguir el mouse y detectar release
        self.root.bind("<B1-Motion>", self.mover_drag)
        self.root.bind("<ButtonRelease-1>", self.detectar_drop)
    
    def mover_drag(self, event):
        """Mueve el label de drag"""
        if self.drag_label:
            self.drag_label.place(x=event.x_root - self.root.winfo_rootx(), 
                                 y=event.y_root - self.root.winfo_rooty())
    
    def detectar_drop(self, event):
        """Detecta dónde se soltó el técnico"""
        if not self.dragging:
            return
        
        # Limpiar el drag visual
        if self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None
        self.root.unbind("<B1-Motion>")
        self.root.unbind("<ButtonRelease-1>")
        
        # Encontrar el widget bajo el cursor
        x = event.x_root
        y = event.y_root
        widget = self.root.winfo_containing(x, y)
        
        # Buscar si el widget tiene asociada una fecha
        if widget and hasattr(widget, 'fecha_asignada'):
            fecha = widget.fecha_asignada
            
            # Si es un festivo que cae en fin de semana, preguntar
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
            self.dibujar_calendario()
        else:
            # No se soltó sobre un área válida
            self.dragging = None
    
    def soltar_tecnico(self, event, fecha):
        """Asigna el técnico arrastrado a una fecha (método alternativo)"""
        if self.dragging:
            # Si es un festivo que cae en fin de semana, preguntar
            if fecha.weekday() >= 5 and fecha in self.festivos:
                if not messagebox.askyesno("Confirmar", 
                    f"Este festivo cae en fin de semana.\n¿Asignar guardia de fin de semana a {self.dragging['tecnico']}?"):
                    return
            
            self.asignaciones[fecha] = {
                'tecnico': self.dragging['tecnico'],
                'color': self.dragging['color']
            }
            self.dibujar_calendario()
    
    def quitar_asignacion(self, fecha):
        """Quita la asignación de una fecha (doble clic)"""
        if fecha in self.asignaciones:
            del self.asignaciones[fecha]
            self.dibujar_calendario()
    
    def actualizar_contador_guardias(self):
        """Actualiza la tabla de contador de guardias del mes actual"""
        # Limpiar tabla anterior
        for widget in self.tabla_contador_frame.winfo_children():
            widget.destroy()
        
        # Contar guardias por técnico en el mes actual
        contador = {}  # {tecnico: {'dias': [dia1, dia2, ...], 'total': x.x}}
        
        for fecha, datos in self.asignaciones.items():
            if fecha.year == self.year and fecha.month == self.month:
                tecnico = datos['tecnico']
                if tecnico not in contador:
                    contador[tecnico] = {'dias': [], 'total': 0}
                
                # Verificar si es una guardia de "TARDE" (0.5 días)
                es_tarde = fecha in self.festivos and "TARDE" in self.festivos[fecha].upper()
                
                contador[tecnico]['dias'].append(fecha.day)
                contador[tecnico]['total'] += 0.5 if es_tarde else 1
        
        if not contador:
            tk.Label(self.tabla_contador_frame, text="Sin guardias este mes", 
                    font=("Arial", 9, "italic"), fg="#999", bg="white").pack(pady=20)
            return
        
        # Encabezados
        header_frame = tk.Frame(self.tabla_contador_frame, bg="#34495e")
        header_frame.pack(fill=tk.X, padx=2, pady=2)
        
        tk.Label(header_frame, text="Técnico", font=("Arial", 9, "bold"), 
                bg="#34495e", fg="white", width=10, anchor="w", padx=5).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Días", font=("Arial", 9, "bold"), 
                bg="#34495e", fg="white", width=8, anchor="w", padx=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(header_frame, text="Total", font=("Arial", 9, "bold"), 
                bg="#34495e", fg="white", width=5, anchor="center").pack(side=tk.LEFT)
        
        # Ordenar por nombre de técnico
        colores_tecnicos = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        
        for i, (tecnico, info) in enumerate(sorted(contador.items())):
            # Obtener el color del técnico
            idx_tecnico = self.tecnicos.index(tecnico) if tecnico in self.tecnicos else 0
            color = colores_tecnicos[idx_tecnico % len(colores_tecnicos)]
            
            row_bg = "#ecf0f1" if i % 2 == 0 else "white"
            row_frame = tk.Frame(self.tabla_contador_frame, bg=row_bg, relief=tk.FLAT, bd=1)
            row_frame.pack(fill=tk.X, padx=2, pady=1)
            
            # Nombre del técnico con su color
            nombre_label = tk.Label(row_frame, text=tecnico, font=("Arial", 9, "bold"), 
                                   bg=color, fg="white", width=10, anchor="w", padx=5)
            nombre_label.pack(side=tk.LEFT)
            
            # Días (ordenados)
            dias_str = ",".join(map(str, sorted(info['dias'])))
            tk.Label(row_frame, text=dias_str, font=("Arial", 9), 
                    bg=row_bg, fg="#2c3e50", anchor="w", padx=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            # Total
            total_str = str(info['total']) if info['total'] % 1 != 0 else str(int(info['total']))
            tk.Label(row_frame, text=total_str, font=("Arial", 9, "bold"), 
                    bg=row_bg, fg="#2c3e50", width=5, anchor="center").pack(side=tk.LEFT)
    
    def mes_anterior(self):
        """Navega al mes anterior"""
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.dibujar_calendario()
    
    def mes_siguiente(self):
        """Navega al mes siguiente"""
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.dibujar_calendario()
    
    def limpiar_asignaciones(self):
        """Limpia todas las asignaciones"""
        if messagebox.askyesno("Confirmar", "¿Borrar todas las asignaciones?"):
            self.asignaciones = {}
            self.dibujar_calendario()
    
    def auto_asignar(self):
        """Auto-asigna técnicos siguiendo reglas de bloques consecutivos"""
        if not messagebox.askyesno("Auto-asignar", 
            "Esto asignará automáticamente técnicos siguiendo las reglas:\n" +
            "- No se asigna el mismo técnico a bloques separados consecutivos\n" +
            "- Bloques de 3 días: mismo técnico\n" +
            "- Bloques de 4+ días: se dividen en sub-bloques de 2 días\n\n¿Continuar?"):
            return
        
        # Validar fechas
        try:
            fecha_inicio = datetime.strptime(self.fecha_inicio_var.get(), "%d/%m/%Y").date()
            fecha_fin = datetime.strptime(self.fecha_fin_var.get(), "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido.\nUse DD/MM/AAAA")
            return
        
        if fecha_fin < fecha_inicio:
            messagebox.showerror("Error", "La fecha de fin debe ser posterior a la fecha de inicio")
            return
        
        # Limpiar asignaciones actuales
        self.asignaciones = {}
        
        # 1. Identificar todos los días que requieren guardia (fines de semana + festivos laborables)
        dias_guardia = set()
        
        # Añadir todos los sábados y domingos en el rango de fechas
        fecha = fecha_inicio
        while fecha <= fecha_fin:
            if fecha.weekday() in [5, 6]:  # Sábado o Domingo
                dias_guardia.add(fecha)
            fecha += timedelta(days=1)
        
        # Añadir festivos laborables (lunes a viernes) dentro del rango
        for fecha_festivo in self.festivos.keys():
            if fecha_inicio <= fecha_festivo <= fecha_fin and fecha_festivo.weekday() < 5:
                dias_guardia.add(fecha_festivo)
        
        # 2. Agrupar días consecutivos en bloques
        dias_ordenados = sorted(dias_guardia)
        bloques = []
        bloque_actual = []
        
        for i, dia in enumerate(dias_ordenados):
            if not bloque_actual:
                bloque_actual = [dia]
            else:
                # Verificar si es consecutivo al último día del bloque
                if (dia - bloque_actual[-1]).days == 1:
                    bloque_actual.append(dia)
                else:
                    # Guardar bloque anterior y empezar uno nuevo
                    bloques.append(bloque_actual)
                    bloque_actual = [dia]
        
        # Añadir el último bloque
        if bloque_actual:
            bloques.append(bloque_actual)
        
        # 3. Aplicar reglas de asignación
        # Obtener el índice del siguiente técnico después del último seleccionado
        ultimo_tecnico = self.ultimo_tecnico_var.get()
        if ultimo_tecnico in self.tecnicos:
            indice_ultimo = self.tecnicos.index(ultimo_tecnico)
            indice_tecnico = (indice_ultimo + 1) % len(self.tecnicos)
        else:
            indice_tecnico = 0
        
        ultimo_tecnico_asignado = None
        
        for bloque in bloques:
            num_dias = len(bloque)
            
            # Verificar que no asignemos el mismo técnico que el bloque anterior
            tecnico_inicial = indice_tecnico
            if ultimo_tecnico_asignado is not None:
                while self.tecnicos[indice_tecnico] == ultimo_tecnico_asignado:
                    indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
                    # Evitar bucle infinito si solo hay un técnico
                    if indice_tecnico == tecnico_inicial:
                        break
            
            if num_dias <= 2:
                # Bloque de 1-2 días: asignar al mismo técnico
                tecnico = self.tecnicos[indice_tecnico]
                color = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"][indice_tecnico % 6]
                for dia in bloque:
                    self.asignaciones[dia] = {'tecnico': tecnico, 'color': color}
                ultimo_tecnico_asignado = tecnico
                indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
            
            elif num_dias == 3:
                # Bloque de 3 días: mismo técnico para los 3
                tecnico = self.tecnicos[indice_tecnico]
                color = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"][indice_tecnico % 6]
                for dia in bloque:
                    self.asignaciones[dia] = {'tecnico': tecnico, 'color': color}
                ultimo_tecnico_asignado = tecnico
                indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
            
            else:
                # Bloque de 4+ días: dividir en sub-bloques de 2 días
                i = 0
                while i < num_dias:
                    # Asegurar que no repetimos técnico del sub-bloque anterior
                    if i > 0:
                        # Cambiar de técnico para el siguiente sub-bloque
                        indice_tecnico = (indice_tecnico + 1) % len(self.tecnicos)
                    
                    tecnico = self.tecnicos[indice_tecnico]
                    color = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"][indice_tecnico % 6]
                    
                    # Asignar 2 días (o lo que quede si es menos)
                    dias_asignar = min(2, num_dias - i)
                    for j in range(dias_asignar):
                        self.asignaciones[bloque[i + j]] = {'tecnico': tecnico, 'color': color}
                    
                    ultimo_tecnico_asignado = tecnico
                    i += dias_asignar
        
        self.dibujar_calendario()
        messagebox.showinfo("Completado", 
            f"✅ Asignación automática completada\n\n" +
            f"Bloques procesados: {len(bloques)}\n" +
            f"Días asignados: {len(self.asignaciones)}")
    
    def exportar_csv(self):
        """Exporta las asignaciones a CSV de Google Calendar"""
        if not self.asignaciones:
            messagebox.showwarning("Advertencia", "No hay asignaciones para exportar")
            return
        
        # Ordenar asignaciones por fecha
        asignaciones_ordenadas = sorted(self.asignaciones.items(), key=lambda x: x[0])
        
        # Agrupar fines de semana (sábado-domingo consecutivos del mismo técnico)
        eventos = []
        i = 0
        while i < len(asignaciones_ordenadas):
            fecha, datos = asignaciones_ordenadas[i]
            tecnico = datos['tecnico']
            
            # Verificar si es sábado y el domingo siguiente tiene el mismo técnico
            if fecha.weekday() == 5:  # Sábado
                fecha_domingo = fecha + timedelta(days=1)
                if i + 1 < len(asignaciones_ordenadas):
                    siguiente_fecha, siguiente_datos = asignaciones_ordenadas[i + 1]
                    if siguiente_fecha == fecha_domingo and siguiente_datos['tecnico'] == tecnico:
                        # Guardia de fin de semana (sábado-domingo)
                        eventos.append({
                            'fecha_inicio': fecha,
                            'fecha_fin': fecha_domingo,
                            'tecnico': tecnico,
                            'subject': f"Guardia - {tecnico}"
                        })
                        i += 2
                        continue
            
            # Guardia individual
            anotacion = self.festivos.get(fecha, "")
            if anotacion:
                subject = f"Guardia {anotacion} - {tecnico}"
            else:
                subject = f"Guardia - {tecnico}"
            
            eventos.append({
                'fecha_inicio': fecha,
                'fecha_fin': fecha,
                'tecnico': tecnico,
                'subject': subject
            })
            i += 1
        
        # Escribir CSV
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
                    evento['fecha_inicio'].strftime("%Y-%m-%d"),
                    "00:00:00",
                    evento['fecha_fin'].strftime("%Y-%m-%d"),
                    "23:59:59",
                    "False",
                    "",
                    "",
                    "False"
                ])
        
        messagebox.showinfo("Éxito", 
            f"✅ CSV exportado correctamente\n\nArchivo: {nombre_archivo}\nEventos: {len(eventos)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GuardiasGUI(root)
    root.mainloop()
