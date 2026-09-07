# 01 — Stack y arquitectura

Estas decisiones son **firmes**. No las cambies salvo error técnico insalvable; en ese caso
elige la alternativa más estándar y documenta el motivo en un comentario.

## Stack

### Backend
- **Node.js 20+** con **TypeScript**.
- **Express** para la API REST.
- **googleapis** (paquete oficial) para Google Calendar (OAuth2 + Calendar API).
- **openai** (paquete oficial) para GPT.
- **dotenv** para variables de entorno.
- Persistencia: **ficheros JSON en disco** (sin base de datos), reutilizando el formato actual.
- **zod** para validar payloads de entrada.

### Frontend
- **React 18 + TypeScript + Vite**.
- **CSS plano/módulos CSS** (sin librería de componentes pesada) para controlar el aspecto y
  parecerse a la app de escritorio. Puedes usar variables CSS para la paleta.
- Drag & drop: **@dnd-kit/core** (moderno, accesible) para arrastrar técnicos a los días.
- Estado de servidor: **@tanstack/react-query** para fetching/cache; estado local con hooks.
- Router: **react-router-dom** (dos rutas: `/generador` y `/visualizador`, con `/generador` por defecto).

### Comunicación
- El frontend habla con el backend por **REST/JSON** bajo el prefijo **`/api`**.
- En desarrollo, Vite corre en `5173` y proxya `/api` al backend en `3001`.
- En producción, el backend sirve el build estático del frontend.

## Estructura de carpetas objetivo

```
webapp/
  README.md
  docs/                      # (ya creada) — especificación
  .env.example               # plantilla de variables (crear)
  package.json               # scripts raíz (workspaces o concurrently)
  server/
    package.json
    tsconfig.json
    src/
      index.ts               # arranque Express, sirve /api y estáticos en prod
      config.ts              # carga .env, rutas de datos
      routes/
        tecnicos.ts
        festivos.ts
        guardias.ts          # CRUD guardias + estadísticas + import/export CSV
        google.ts            # auth status, login, calendarios, sync push/pull
        gpt.ts               # generar guardias
      services/
        store.ts             # lectura/escritura de calendarios.json (equiv. CalendarManager)
        tecnicos.ts          # parse tecnicos.txt
        festivos.ts          # parse festivos.txt
        csv.ts               # import/export CSV (formato Google)
        googleCalendar.ts    # OAuth2 + push/pull (equiv. google_calendar_sync.py)
        gpt.ts               # prompt + parsing (equiv. gpt_assign.py)
      types.ts
    data/                    # ficheros de datos (ver 02-DATA-MODELS)
      tecnicos.txt
      festivos.txt
      calendarios.json
      google_config.json     # generado al configurar
      google_credentials.json# NO versionar
      google_token.json      # NO versionar, generado tras OAuth
  client/
    package.json
    tsconfig.json
    vite.config.ts           # proxy /api -> 3001
    index.html
    src/
      main.tsx
      App.tsx                # layout con navegación entre pestañas
      api/                   # wrappers fetch por recurso
      hooks/
      components/
        MonthCalendar.tsx    # calendario editable (Generador)
        MultiMonthViewer.tsx # vista multi-mes (Visualizador)
        TechnicianPalette.tsx# técnicos arrastrables
        StatsPanel.tsx       # estadísticas por técnico
        GptOverlay.tsx       # overlay "Crear desde GPT"
        GoogleConfigModal.tsx
        Toast.tsx / Modal.tsx# utilidades UI
      pages/
        GeneratorPage.tsx
        ViewerPage.tsx
      styles/
        theme.css            # paleta (ver 07-UI-UX)
```

## Datos: dónde viven

- Copia los ficheros de referencia de la app de escritorio a `server/data/` al construir:
  - `../desktop/tecnicos.txt` → `server/data/tecnicos.txt`
  - `../desktop/festivos.txt` → `server/data/festivos.txt`
  - `../desktop/json/calendarios.json` → `server/data/calendarios.json`
- **No copies** `google_credentials.json`, `google_token.json` ni `.env` (contienen secretos).
  El usuario los colocará. Documenta en `webapp/README` (o en `.env.example`) dónde van.
- La ruta base de datos debe ser **configurable** por env (`DATA_DIR`, por defecto `server/data`).

## Variables de entorno (`webapp/.env.example` a crear)

```
# Servidor
PORT=3001
DATA_DIR=./server/data

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Google OAuth (fichero de credenciales tipo "OAuth client" descargado de Google Cloud)
GOOGLE_CREDENTIALS_FILE=./server/data/google_credentials.json
GOOGLE_TOKEN_FILE=./server/data/google_token.json
GOOGLE_CONFIG_FILE=./server/data/google_config.json
# URI de callback OAuth (debe coincidir con la registrada en Google Cloud)
GOOGLE_OAUTH_REDIRECT=http://localhost:3001/api/google/oauth/callback
```

## Scripts (raíz `webapp/package.json`)

- `npm run dev` — arranca server (ts-node-dev/tsx) y client (vite) en paralelo (usar `concurrently`).
- `npm run build` — build de client (vite) y compilación de server (tsc).
- `npm start` — arranca el server compilado sirviendo el build del client.
- `npm run install:all` — instala dependencias de `server/` y `client/`.

Usa **npm** (no pnpm/yarn) salvo que detectes ya configurado lo contrario.

## Puertos y CORS

- Dev: client `5173`, server `3001`. Proxy en Vite evita problemas de CORS.
- Si añades CORS en Express, permite `http://localhost:5173` en desarrollo.
