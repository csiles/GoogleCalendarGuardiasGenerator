# Google Calendar Guardias Generator

Generador de guardias de soporte con interfaz gráfica para asignación y exportación a Google Calendar.

## Características

- **Interfaz gráfica intuitiva** con drag-and-drop
- **Auto-asignación inteligente** de guardias con reglas de distribución
- **Prevención de guardias consecutivas**
- **Detección automática** de festivos y fines de semana
- **Exportación a CSV** compatible con Google Calendar
- **Contador de guardias** por técnico y mes

## Requisitos

- Python 3.7+
- tkinter (incluido en Python estándar)

## Uso

```bash
python generator_gui.py
```

## Archivos de configuración

- `tecnicos.txt`: Lista de técnicos disponibles (uno por línea)
- `festivos.txt`: Fechas festivas en formato DD/MM/YYYY

## Exportación

El CSV generado es compatible con la importación de Google Calendar.
