# 05 — Integración con Google Calendar

Referencia Python: `../desktop/utils/google_calendar_sync.py`. Replica la misma lógica con el
paquete Node **`googleapis`**.

## Scope y ficheros
- Scope: `https://www.googleapis.com/auth/calendar`.
- Credenciales OAuth: `GOOGLE_CREDENTIALS_FILE` (aportado por el usuario).
- Token: `GOOGLE_TOKEN_FILE` (se genera tras el login; contiene access + refresh token).
- Config calendario: `GOOGLE_CONFIG_FILE` (`google_config.json`).

## Diferencia clave respecto a la app de escritorio
La app de escritorio usa `run_local_server(port=0)` (flujo instalado). En web usaremos el
**flujo OAuth2 con redirect URI** (`GOOGLE_OAUTH_REDIRECT`). Pasos:

1. `GET /api/google/oauth/login`: crea un `OAuth2Client` con client_id/secret del fichero de
   credenciales y `redirect_uri = GOOGLE_OAUTH_REDIRECT`. Genera `authUrl` con
   `access_type: 'offline'`, `prompt: 'consent'`, `scope: [calendar]`. Devuelve `{ url }`.
2. El usuario autoriza; Google redirige a `GET /api/google/oauth/callback?code=...`.
3. Intercambia `code` por tokens (`getToken`), guarda el token en `GOOGLE_TOKEN_FILE`
   (incluyendo `refresh_token`). Responde una página "Autenticación completada".
4. En cada uso, carga el token; si expiró y hay refresh_token, refresca automáticamente
   (googleapis lo hace si configuras el client con las credenciales y el token).

> El usuario debe registrar `http://localhost:3001/api/google/oauth/callback` como URI de
> redirección autorizado en Google Cloud Console. Indícalo en `webapp/README` / `.env.example`.

## Listar calendarios (`GET /api/google/calendars`)
`calendar.calendarList.list()` → filtra los que tienen `accessRole` ∈ {`owner`,`writer`}.
Devuelve `{ id, name(summary), access_role, is_primary(primary), description, timezone(timeZone||'Europe/Madrid') }`.

## Push: Local → Google (`POST /api/google/sync/push`)
Para cada evento del store (`getAllEvents()`), construir el cuerpo Google:
```js
{
  summary: evento.titulo,
  description: evento.descripcion || '',
  start: { date: evento.fecha, timeZone: 'Europe/Madrid' },
  end:   { date: <fecha + 1 día>, timeZone: 'Europe/Madrid' },   // all-day, end exclusivo
  source: { title: 'Guardias Generator', url: 'https://github.com/csiles/GoogleCalendarGuardiasGenerator' },
  colorId: <map color hex del técnico → id Google, opcional>
}
```
Lógica de create/update (igual que escritorio `sync_event`):
- Si el evento tiene `google_event_id` → `events.update(calendarId, eventId, body)`.
- Si no, **buscar duplicado**: `events.list` con `timeMin`/`timeMax` cubriendo ese día
  (all-day: `[fecha, fecha+1)`), `singleEvents: true`; si hay uno con `summary` == `titulo`
  (case-insensitive) → update de ese; si no → `events.insert`.
- Guarda en el store el `google_event_id` (result.id) y `google_link` (result.htmlLink) del
  evento correspondiente (match por fecha+titulo), y persiste.
- Acumula stats `{ total, created, updated, errors, errores_detalle }`.
- Devuelve stats + `calendar_url` = `https://calendar.google.com/calendar/embed?src=<calendar_id>`.

### Mapa de color hex → colorId Google (de escritorio)
```
'#3498db': '9', '#e74c3c': '11', '#2ecc71': '10', '#f39c12': '6', '#9b59b6': '3', '#1abc9c': '7'
```
Si el color del técnico no está en el mapa, omite `colorId`.

## Pull: Google → Local (`POST /api/google/sync/pull`)
- Rango **fijo**: `timeMin = hoy − 365 días`, `timeMax = hoy + 180 días` (formato RFC3339,
  p.ej. `YYYY-MM-DDT00:00:00Z` / `...T23:59:59Z`).
- `events.list({ calendarId, timeMin, timeMax, maxResults: 2500, singleEvents: true, orderBy: 'startTime' })`.
- Por cada evento: fecha = `start.date` (all-day) o `start.dateTime.slice(0,10)`.
- Convertir a evento local (importar **sin preguntar**, ver `03 §Sincronización`):
  - `titulo = summary || 'Sin título'`.
  - Si `titulo` casa `^Guardia\s*-\s*(.+)$` → `tecnico = match[1].trim()`, `tipo = 'guardia'`.
    Si no → `tecnico = null`, `tipo = 'otro'`.
  - `id = MD5(fecha_titulo)[:16]`, `origen = 'google_pull'`, `google_event_id = event.id`,
    `google_link = event.htmlLink`.
  - `addEvent(fecha, evento)` (respeta dedupe por id).
- Clasifica para el resumen: técnico activo (existe en `tecnicos.txt`), técnico eliminado
  (tiene técnico pero no existe → 💀), genérico (sin técnico).
- Persiste el store. Devuelve el resumen (ver `04`).

## Eliminar evento
Existe `delete_event(google_event_id)` en escritorio pero **no se usa en borrados locales**
(se dejó de usar a propósito: editar/borrar local no debe tocar Google). No expongas borrado
directo a Google salvo que definas una acción explícita; por defecto **no lo implementes**.
