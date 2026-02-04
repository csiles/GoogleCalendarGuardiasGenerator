"""
Pestaña de visualización de calendarios históricos y futuros
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from models.calendar_manager import CalendarManager
from ui.components.multi_month_viewer import MultiMonthViewer
from utils.file_utils import get_technician_colors, load_tecnicos


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
        
        tk.Label(header, text="📖 Visualizador de Calendarios Históricos", 
                font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(pady=10)
    
    def _create_toolbar(self):
        """Crea la barra de herramientas"""
        toolbar = tk.Frame(self, bg="#34495e", height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        btn_frame = tk.Frame(toolbar, bg="#34495e")
        btn_frame.pack(pady=10)
        
        # Botón importar CSV
        tk.Button(btn_frame, text="📁 Importar CSV", command=self._import_csv,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Botón actualizar
        tk.Button(btn_frame, text="🔄 Actualizar", command=self._refresh_view,
                 bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                 relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
    
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
        self.multi_month_viewer.refresh()
        self._update_status()
        messagebox.showinfo("Actualizado", "Vista actualizada correctamente")
    
    def _update_status(self):
        """Actualiza la barra de estado"""
        stats = self.calendar_manager.get_statistics()
        text = f"Total eventos: {stats['total_eventos']} | Meses: {stats['total_meses_con_datos']} | Última actualización: {stats['ultima_actualizacion'][:19]}"
        self.status_label.config(text=text)
