# 00 — Overview

## Qué es

Aplicación para **gestionar las guardias de fin de semana/festivos del equipo de Soporte**
y sincronizarlas con **Google Calendar**. Tiene dos grandes áreas:

1. **Generador de guardias**: crear/editar asignaciones de técnicos sobre un mes concreto
   (arrastrando técnicos a días), generar asignaciones automáticamente con **GPT**, y exportar
   a CSV.
2. **Visualizador de calendarios**: vista de varios meses a la vez, importar CSV, y
   **sincronización bidireccional con Google Calendar** (local → Google y Google → local).

Los datos de guardias se **persisten en JSON** en el servidor y se pueden subir/bajar de
Google Calendar bajo demanda (nunca automáticamente al editar).

## Actores y datos de entrada

- **Técnicos**: lista ordenada con un color por técnico (fichero `tecnicos.txt`).
- **Festivos**: lista de fechas con anotación opcional (fichero `festivos.txt`).
- **Guardias**: eventos por día almacenados en `calendarios.json`.
- **Config Google**: calendario seleccionado (`google_config.json`) + credenciales OAuth.
- **Config GPT**: `OPENAI_API_KEY` en `.env`.

## Objetivos de la versión web

- **Paridad funcional total** con `../desktop/` (ver `03-FUNCTIONAL-SPEC.md`).
- **Misma semántica de datos** (ver `02-DATA-MODELS.md`) para compatibilidad.
- **Mejor UX** donde el web lo permita: navegación fluida, drag & drop moderno, edición inline,
  responsividad, y feedback visual claro. Se anima a mejorar estética y ergonomía siempre que
  no se pierda ninguna funcionalidad.

## Fuente de verdad

El código Python en `../desktop/` es la referencia de comportamiento. Ficheros clave:

- `../desktop/main.py` — arranque y pestañas.
- `../desktop/ui/generator_tab.py` — pestaña Generador (calendario editable, drag&drop, export CSV, botón "Crear desde GPT").
- `../desktop/ui/viewer_tab.py` — pestaña Visualizador (multi-mes, import CSV, sincronización Google, config).
- `../desktop/ui/components/multi_month_viewer.py` — render multi-mes, edición por click/drag, estadísticas por técnico, marca de técnico eliminado (💀).
- `../desktop/ui/dialogs/calendar_config_dialog.py` — selección de calendario Google.
- `../desktop/ui/dialogs/gpt_assign_dialog.py` — overlay "Crear desde GPT".
- `../desktop/models/calendar_manager.py` — persistencia JSON, import CSV, estadísticas.
- `../desktop/utils/google_calendar_sync.py` — OAuth2 + push/pull Google Calendar.
- `../desktop/utils/gpt_assign.py` — prompt y parsing de la respuesta de GPT.
- `../desktop/utils/file_utils.py` — lectura de `tecnicos.txt` y `festivos.txt`.
