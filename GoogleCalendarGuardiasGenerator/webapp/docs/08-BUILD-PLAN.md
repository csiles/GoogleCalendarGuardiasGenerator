# 08 — Plan de construcción (para el agente, en orden)

Ejecuta estos pasos **en orden**. Tras cada fase, verifica que compila/arranca antes de seguir.
No pidas confirmación al usuario. Si algo del entorno falta (credenciales Google, API key),
implementa el comportamiento degradado documentado (endpoints devuelven `503`/estado
`configured:false`) y continúa.

## Fase 0 — Preparación
1. Lee todos los docs `00`→`07`.
2. Crea `webapp/.env.example` con el contenido de `01-STACK-AND-ARCHITECTURE.md §Variables`.
3. Crea `webapp/.gitignore` que ignore: `node_modules/`, `dist/`, `.env`,
   `server/data/google_credentials.json`, `server/data/google_token.json`,
   `server/data/google_config.json`, `server/data/calendarios.json` (opcional), `*.log`.
4. Copia los ficheros de datos de referencia:
   - `../desktop/tecnicos.txt` → `server/data/tecnicos.txt`
   - `../desktop/festivos.txt` → `server/data/festivos.txt`
   - `../desktop/json/calendarios.json` → `server/data/calendarios.json`

## Fase 1 — Backend base
1. Inicializa `server/` (npm, TypeScript, Express, zod, dotenv). Configura `tsconfig`, scripts
   `dev` (tsx/ts-node-dev) y `build`/`start`.
2. `config.ts`: carga `.env`, resuelve rutas de `DATA_DIR` y ficheros.
3. `services/store.ts`: implementa el equivalente a `CalendarManager` (ver `02-DATA-MODELS §3`):
   load/reload/save, addEvent (dedupe por id + estadísticas), getAllEvents, getStatistics,
   updateGoogleEventId, deleteDay, deleteMonth. `id = md5(`${fecha}_${titulo}`).slice(0,16)`.
4. `services/tecnicos.ts` y `services/festivos.ts`: parseo de los `.txt` (ver `02 §1,§2`).
5. Rutas `tecnicos`, `festivos`, `guardias`, `health`. Prueba con `curl`/REST que devuelven datos.

## Fase 2 — CSV
1. `services/csv.ts`: export (all-day, End exclusivo, agrupar sáb+dom mismo técnico/tipo) e import
   (dedupe por hash MD5 del fichero + por día ocupado; extraer técnico tras último `" - "`).
2. Rutas `POST /api/csv/import`, `POST /api/csv/export`.
3. Verifica round-trip: exportar unas guardias, reimportarlas y comprobar coherencia.

## Fase 3 — Frontend base
1. Inicializa `client/` (Vite + React + TS). Configura proxy `/api` → `http://localhost:3001`.
2. Layout `App.tsx` con pestañas y router (`/generador`, `/visualizador`).
3. `theme.css` con la paleta de `07-UI-UX.md`. Wrappers `api/` con fetch + react-query.
4. Página **Generador**: panel de control, calendario mensual editable con dnd-kit, paleta de
   técnicos, panel de estadísticas, botones Limpiar/Exportar CSV. (GPT y "Crear desde GPT" en Fase 5.)
5. Página **Visualizador**: multi-mes (7), navegación, estadísticas, marca 💀; Importar CSV y
   Actualizar funcionando contra el backend. (Google en Fase 4.)

## Fase 4 — Google Calendar
1. `services/googleCalendar.ts`: OAuth2 con redirect (ver `05`), listCalendars, push, pull.
2. Rutas `google`: status, oauth/login, oauth/callback, calendars, config, sync/push, sync/pull.
3. Frontend: etiqueta "Calendario seleccionado", botón "Login/config" → modal de selección,
   botones de sync con resúmenes en modal/toast. Barra de estado con estado de Google.
4. Comportamiento degradado si no hay credenciales/token: `status` refleja `configured/authenticated:false`
   y los botones de sync quedan deshabilitados con tooltip explicativo.

## Fase 5 — GPT
1. `services/gpt.ts`: `REGLAS_TEXT_DEFAULT`, build_prompt, generar, parse (ver `06`).
2. Rutas `gpt`: status, reglas-default, generar.
3. Frontend: overlay "Crear desde GPT" (2 vistas), botón "Crear desde GPT" en el Generador,
   guardado vía `POST /api/guardias/bulk`.

## Fase 6 — Pulido y verificación
1. Recorre el **checklist de paridad** de `03-FUNCTIONAL-SPEC.md` y marca cada punto.
2. Toasts/errores consistentes. Estados de carga. Responsividad razonable.
3. Actualiza `webapp/README.md` con instrucciones de instalación/arranque reales
   (comandos, dónde poner credenciales Google, URI de callback en Google Cloud, API key).
4. Verifica: `npm run install:all`, `npm run dev` arranca ambos; `npm run build` + `npm start`
   sirve la app en producción sin errores de compilación TypeScript.

## Criterios de "hecho"
- Todas las casillas del checklist de paridad cumplidas.
- `tsc` sin errores en server y client. La app arranca en dev y en prod.
- Los formatos de datos escritos por la web son **leídos correctamente por la app de escritorio**
  (mismo `calendarios.json`).
- README con pasos reproducibles.

## Notas de compatibilidad y riesgos
- **Zona horaria**: usa `Europe/Madrid` para eventos all-day, como escritorio.
- **all-day End exclusivo**: no te equivoques con el ±1 día (fuente de bugs).
- **id determinista**: mismo algoritmo MD5 que escritorio o se romperá el dedupe/cruce con datos existentes.
- **No tocar Google al editar/borrar local**: solo los botones de sync mueven datos.
- **Secretos**: nunca versionar `.env`, `google_credentials.json`, `google_token.json`.
