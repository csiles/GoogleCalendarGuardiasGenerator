# Google Calendar Guardias Generator

Generador de guardias de soporte con interfaz gráfica para asignación y exportación a Google Calendar.

## 🎯 Características

### Pestaña 1: Generador de Guardias
- **Interfaz gráfica intuitiva** con drag-and-drop
- **Auto-asignación inteligente** de guardias con reglas de distribución
- **Prevención de guardias consecutivas**
- **Detección automática** de festivos y fines de semana
- **Exportación a CSV** compatible con Google Calendar
- **Contador de guardias** por técnico y mes

### Pestaña 2: Visor de Calendarios
- **Vista multi-mes**: Visualiza 7 meses simultáneamente (3 atrás + actual + 3 adelante)
- **Importación CSV**: Importa calendarios exportados previamente
- **Persistencia JSON**: Los datos se guardan automáticamente
- **Navegación temporal**: Navega por meses/años fácilmente
- **Estadísticas globales**: Visualiza métricas de todos los calendarios

## 🏗️ Arquitectura

El proyecto sigue principios **SOLID** y **KISS** con una estructura modular:

```
GoogleCalendarGuardiasGenerator/
├── models/              # Lógica de negocio
│   ├── calendar_manager.py    # Gestor de calendarios con persistencia
│   └── __init__.py
├── ui/                  # Componentes de interfaz
│   ├── components/      # Widgets reutilizables
│   │   ├── multi_month_viewer.py
│   │   └── __init__.py
│   ├── generator_tab.py        # Pestaña de generación
│   ├── viewer_tab.py           # Pestaña de visualización
│   └── __init__.py
├── utils/               # Utilidades compartidas
│   ├── file_utils.py           # Lectura de archivos de config
│   └── __init__.py
├── json/                # Datos persistidos (auto-generado)
│   └── calendarios.json
├── docs/                # Documentación técnica
│   ├── ANALISIS_GESTOR_CALENDARIOS.md
│   └── CODIGO_EJEMPLO_CALENDARIOS.md
├── main.py              # Punto de entrada principal ⭐
├── generator_gui.py     # Versión original (legacy)
├── tecnicos.txt
├── festivos.txt
└── README.md
```

## 🚀 Uso

### Ejecución

```bash
# Nueva versión modular (recomendada)
python main.py

# Versión original (legacy)
python generator_gui.py
```

### Flujo de trabajo típico

1. **Generar Guardias** (Pestaña 1)
   - Configura período de fechas
   - Usa drag-and-drop o auto-asignar
   - Exporta a CSV

2. **Visualizar Histórico** (Pestaña 2)
   - Importa CSV exportado
   - Navega por meses anteriores/futuros
   - Consulta estadísticas

## 📋 Requisitos

- Python 3.7+
- tkinter (incluido en Python estándar)

## 📁 Archivos de configuración

- `tecnicos.txt`: Lista de técnicos disponibles (uno por línea)
- `festivos.txt`: Fechas festivas en formato `DD/MM/YYYY,ANOTACION`

## 📤 Exportación

El CSV generado es compatible con la importación de Google Calendar.

## 🔮 Próximas Funcionalidades

- [ ] Integración con Google Calendar API (sincronización bidireccional)
- [ ] Notificaciones por email
- [ ] Generación de informes PDF

## 📝 Changelog

### v1.1.0 (Actual)
- ✨ Refactorización modular siguiendo SOLID/KISS
- ✨ Nueva pestaña de visualización de calendarios históricos
- ✨ CalendarManager con persistencia JSON
- ✨ Vista multi-mes (7 meses simultáneos)
- ✨ Importación de CSV con detección de duplicados

### v1.0.0
- 🎉 Versión inicial con generador GUI
- ✅ Drag-and-drop de técnicos
- ✅ Auto-asignación con reglas de bloques
- ✅ Exportación a CSV para Google Calendar
