"""
Punto de entrada de la aplicación - Gestor de Guardias con pestañas
"""

import tkinter as tk
from tkinter import ttk
from ui.generator_tab import GeneratorTab
from ui.viewer_tab import ViewerTab


class GuardiasApplication:
    """Aplicación principal con pestañas"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Guardias - Soporte IT-Leisure")
        self.root.geometry("1600x850")
        
        self._create_notebook()
    
    def _create_notebook(self):
        """Crea el notebook con pestañas"""
        # Estilo para las pestañas
        style = ttk.Style()
        style.theme_use('clam')  # Tema que permite personalización de colores
        
        # Configurar estilo de las pestañas
        style.configure('TNotebook', background='#ecf0f1', borderwidth=0)
        style.configure('TNotebook.Tab', 
                       font=('Arial', 11, 'bold'), 
                       padding=[20, 10],
                       background='#bdc3c7',  # Gris claro
                       foreground='#2c3e50',  # Texto oscuro
                       borderwidth=1,
                       relief='raised')
        
        # Estilo cuando la pestaña está seleccionada
        style.map('TNotebook.Tab',
                 background=[('selected', '#3498db')],  # Azul cuando está seleccionada
                 foreground=[('selected', 'white')],    # Texto blanco cuando está seleccionada
                 padding=[('selected', [20, 10])],      # Mismo padding
                 relief=[('selected', 'raised')])
        
        # Crear notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 1: Generador
        self.generator_tab = GeneratorTab(self.notebook)
        self.notebook.add(self.generator_tab, text="🔧 Generar Guardias")
        
        # Pestaña 2: Visor de calendarios
        self.viewer_tab = ViewerTab(self.notebook)
        self.notebook.add(self.viewer_tab, text="📖 Ver Calendarios")


def main():
    """Función principal"""
    root = tk.Tk()
    app = GuardiasApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
