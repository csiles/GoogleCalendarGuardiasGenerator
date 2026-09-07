"""
Overlay "Crear desde GPT": edita instrucciones, las envía a GPT, muestra la propuesta
de guardias resultante y permite guardarla en el calendario local antes de sincronizar
con Google Calendar desde la pestaña Visualizador.

Se implementa como un Frame superpuesto (con place()) sobre la ventana principal en
lugar de una ventana Toplevel aparte, para que se sienta como parte de la propia app.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Dict, List

from models.calendar_manager import CalendarManager
from utils.gpt_assign import (
    REGLAS_TEXT_DEFAULT, is_configured, build_prompt, generar_guardias, parse_respuesta
)

logger = logging.getLogger(__name__)


class GPTAssignDialog(tk.Frame):
    """Overlay modal (dentro de la propia ventana) para generar guardias con GPT"""

    def __init__(self, parent, tecnicos: List[str], festivos: Dict[date, str],
                 fecha_inicio: date, fecha_fin: date):
        self.root_window = parent.winfo_toplevel()
        super().__init__(self.root_window, bg="#1c1c1c")

        self.tecnicos = tecnicos
        self.festivos = festivos
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.asignaciones_propuestas = []

        # Cubre toda la ventana principal para simular el fondo oscurecido del modal
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.grab_set()

        # Tarjeta centrada con el contenido real del modal
        self.card = tk.Frame(self, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=720, height=620)

        self._build_prompt_view()

    def _close(self):
        self.grab_release()
        self.destroy()

    def _build_prompt_view(self):
        """Vista 1: edición de instrucciones y envío a GPT"""
        for widget in self.card.winfo_children():
            widget.destroy()

        header = tk.Frame(self.card, bg="#2c3e50")
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="Crear guardias con GPT", font=("Arial", 13, "bold"),
                 bg="#2c3e50", fg="white", pady=10, padx=10).pack(side=tk.LEFT)
        tk.Button(header, text="✕", command=self._close, bg="#2c3e50", fg="white",
                  font=("Arial", 11, "bold"), relief=tk.FLAT, cursor="hand2",
                  activebackground="#c0392b", activeforeground="white").pack(side=tk.RIGHT, padx=10)

        tk.Label(self.card,
                 text=f"Rango a asignar: {self.fecha_inicio.strftime('%d/%m/%Y')} - "
                      f"{self.fecha_fin.strftime('%d/%m/%Y')}. Completa 'REGLAS PARTICULARES' si aplica.",
                 font=("Arial", 9), fg="#555", bg="#ecf0f1").pack(anchor="w", padx=10, pady=(8, 0))

        text_frame = tk.Frame(self.card, bg="#ecf0f1")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_instrucciones = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9),
                                           yscrollcommand=scrollbar.set)
        self.text_instrucciones.pack(fill=tk.BOTH, expand=True)
        self.text_instrucciones.insert("1.0", REGLAS_TEXT_DEFAULT)
        scrollbar.config(command=self.text_instrucciones.yview)

        self.status_label = tk.Label(self.card, text="", font=("Arial", 9, "italic"),
                                      fg="#555", bg="#ecf0f1")
        self.status_label.pack(anchor="w", padx=10)

        btn_frame = tk.Frame(self.card, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.btn_enviar = tk.Button(btn_frame, text="Enviar a GPT", command=self._enviar,
                                     bg="#9b59b6", fg="white", font=("Arial", 10, "bold"),
                                     relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=6)
        self.btn_enviar.pack(side=tk.LEFT)

        tk.Button(btn_frame, text="Cancelar", command=self._close,
                  bg="#95a5a6", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=6).pack(side=tk.LEFT, padx=10)

    def _enviar(self):
        if not is_configured():
            messagebox.showerror(
                "GPT no configurado",
                "No se ha encontrado OPENAI_API_KEY.\n\n"
                "Configúrala en el fichero .env de la raíz del proyecto (ver .env.example).",
                parent=self.root_window
            )
            return

        instrucciones = self.text_instrucciones.get("1.0", tk.END).strip()
        if not instrucciones:
            messagebox.showwarning("Sin instrucciones", "El texto de instrucciones está vacío.",
                                    parent=self.root_window)
            return

        self.btn_enviar.config(state=tk.DISABLED, text="Generando...")
        self.status_label.config(text="Consultando a GPT, esto puede tardar unos segundos...")

        def worker():
            try:
                calendar_manager = CalendarManager()
                ultimas_guardias = self._get_ultimas_guardias(calendar_manager, n=10)
                festivos_rango = {
                    f: motivo for f, motivo in self.festivos.items()
                    if self.fecha_inicio <= f <= self.fecha_fin
                }

                prompt = build_prompt(
                    instrucciones, self.tecnicos, festivos_rango,
                    ultimas_guardias, self.fecha_inicio, self.fecha_fin
                )

                texto_respuesta = generar_guardias(prompt)
                asignaciones = parse_respuesta(texto_respuesta)

                self.after(0, lambda: self._mostrar_revision(asignaciones))
            except Exception as e:
                logger.error(f"Error generando guardias con GPT: {e}")
                self.after(0, lambda: self._mostrar_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _mostrar_error(self, error_msg: str):
        self.btn_enviar.config(state=tk.NORMAL, text="Enviar a GPT")
        self.status_label.config(text="")
        messagebox.showerror("Error de GPT", f"No se pudo generar la propuesta:\n\n{error_msg}",
                              parent=self.root_window)

    @staticmethod
    def _get_ultimas_guardias(calendar_manager: CalendarManager, n: int = 10) -> List[dict]:
        """Últimas n guardias (técnico + fecha) ya registradas en local, de más reciente a más antigua"""
        eventos = [
            e for e in calendar_manager.get_all_events()
            if e.get('tipo') == 'guardia' and e.get('tecnico')
        ]
        eventos.sort(key=lambda e: e.get('fecha', ''), reverse=True)
        return [{"fecha": e.get('fecha'), "tecnico": e.get('tecnico')} for e in eventos[:n]]

    def _mostrar_revision(self, asignaciones: List[dict]):
        """Vista 2: tabla de revisión de la propuesta de GPT antes de guardarla en local"""
        self.asignaciones_propuestas = asignaciones

        for widget in self.card.winfo_children():
            widget.destroy()

        header = tk.Frame(self.card, bg="#2c3e50")
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="Propuesta de guardias generada por GPT", font=("Arial", 13, "bold"),
                 bg="#2c3e50", fg="white", pady=10, padx=10).pack(side=tk.LEFT)
        tk.Button(header, text="✕", command=self._close, bg="#2c3e50", fg="white",
                  font=("Arial", 11, "bold"), relief=tk.FLAT, cursor="hand2",
                  activebackground="#c0392b", activeforeground="white").pack(side=tk.RIGHT, padx=10)

        tk.Label(self.card, text="Revisa la propuesta antes de guardarla en el calendario local.",
                 font=("Arial", 9), fg="#555", bg="#ecf0f1").pack(anchor="w", padx=10, pady=(8, 0))

        if not asignaciones:
            tk.Label(self.card, text="GPT no ha devuelto ninguna asignación.",
                      font=("Arial", 10, "italic"), fg="#c0392b", bg="#ecf0f1").pack(pady=20)
            tk.Button(self.card, text="Cerrar", command=self._close,
                      bg="#95a5a6", fg="white", font=("Arial", 10, "bold"),
                      padx=15, pady=6).pack(pady=10)
            return

        table_frame = tk.Frame(self.card, bg="#ecf0f1")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("fecha", "tecnico", "tipo")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        tree.heading("fecha", text="Fecha")
        tree.heading("tecnico", text="Técnico")
        tree.heading("tipo", text="Tipo")
        tree.column("fecha", width=110, anchor="center")
        tree.column("tecnico", width=150, anchor="w")
        tree.column("tipo", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for asignacion in sorted(asignaciones, key=lambda a: a.get('fecha', '')):
            tree.insert("", tk.END, values=(
                asignacion.get('fecha', '?'),
                asignacion.get('tecnico', '?'),
                asignacion.get('tipo', 'guardia')
            ))

        btn_frame = tk.Frame(self.card, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="Guardar en calendario local", command=self._guardar,
                  bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=6).pack(side=tk.LEFT)

        tk.Button(btn_frame, text="Descartar", command=self._close,
                  bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                  relief=tk.RAISED, bd=3, cursor="hand2", padx=15, pady=6).pack(side=tk.LEFT, padx=10)

    def _guardar(self):
        calendar_manager = CalendarManager()
        guardados = 0
        errores = 0

        for asignacion in self.asignaciones_propuestas:
            fecha_str = asignacion.get('fecha')
            tecnico = asignacion.get('tecnico')
            tipo = asignacion.get('tipo', 'guardia')
            if not fecha_str or not tecnico:
                errores += 1
                continue

            try:
                datetime.strptime(fecha_str, "%Y-%m-%d")
            except ValueError:
                errores += 1
                continue

            prefix = "Media Guardia" if tipo == 'media_guardia' else "Guardia"
            titulo = f"{prefix} - {tecnico}"

            year_month = fecha_str[:7]
            day_str = fecha_str[8:10]
            if year_month in calendar_manager.data['meses']:
                if day_str in calendar_manager.data['meses'][year_month]['dias']:
                    calendar_manager.data['meses'][year_month]['dias'][day_str]['eventos'] = []

            evento = {
                'id': calendar_manager._generate_event_id(fecha_str, titulo),
                'titulo': titulo,
                'tecnico': tecnico,
                'tipo': tipo,
                'descripcion': '',
                'all_day': True,
                'origen': 'gpt',
                'fecha_edicion': datetime.now().isoformat()
            }
            calendar_manager.add_event(fecha_str, evento)
            guardados += 1

        calendar_manager.save_data()

        mensaje = f"✅ Guardado en el calendario local\n\nGuardias guardadas: {guardados}"
        if errores:
            mensaje += f"\nEntradas inválidas ignoradas: {errores}"
        mensaje += ("\n\nVe a la pestaña Visualizador y pulsa 'Sincro: Local → Google' "
                    "para subirlas a Google Calendar.")

        messagebox.showinfo("Guardado", mensaje, parent=self.root_window)
        self._close()

