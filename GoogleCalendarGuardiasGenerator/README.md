# Guardias Generator — Monorepo

Gestor de guardias de Soporte con sincronización a Google Calendar.

Este repositorio contiene **dos implementaciones**:

- **`desktop/`** — Aplicación de escritorio en **Python + Tkinter** (la actual, en uso).
  Punto de entrada: `desktop/main.py`. Ver `desktop/README.md`.
- **`webapp/`** — Nueva versión **web (Node.js + React)**, en construcción.
  Toda la especificación para construirla está en `webapp/docs/`. Empieza por `webapp/README.md`.

## Ejecutar la app de escritorio

```powershell
cd desktop
pip install -r requirements.txt
python main.py
```

Requiere, dentro de `desktop/`:
- `.env` con `OPENAI_API_KEY` (para "Crear desde GPT").
- `json/google_credentials.json` (para sincronizar con Google Calendar).

## Construir la app web

La app web aún no está implementada. La documentación completa (spec funcional, modelos de datos,
API, integración Google/GPT, guía visual y plan de construcción) está en `webapp/docs/`.
