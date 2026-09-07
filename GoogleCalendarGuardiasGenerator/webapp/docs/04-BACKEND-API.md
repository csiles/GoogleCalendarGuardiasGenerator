# 04 — Contrato de la API REST (backend)

Prefijo base: **`/api`**. Todo JSON salvo descargas de CSV. Errores con forma:
```json
{ "error": "mensaje legible", "details": "opcional" }
```
Códigos: `200` OK, `400` validación, `404` no encontrado, `409` conflicto, `500` error interno,
`503` dependencia externa no configurada (p.ej. Google/GPT sin credenciales).

Valida los bodies con **zod**.

---

## Técnicos

### `GET /api/tecnicos`
Devuelve la lista **en orden** leída de `tecnicos.txt`.
```json
[ { "nombre": "Pilar", "color": "#3498db" }, { "nombre": "Isa", "color": "#e74c3c" } ]
```

---

## Festivos

### `GET /api/festivos`
```json
[ { "fecha": "2026-03-18", "anotacion": "TARDE" }, { "fecha": "2026-12-25", "anotacion": "" } ]
```

---

## Guardias (store)

### `GET /api/guardias`
Todos los eventos aplanados con `fecha`:
```json
[ { "fecha": "2026-03-07", "id": "4fc5...", "titulo": "Guardia - Pilar", "tecnico": "Pilar", "tipo": "guardia", ... } ]
```
Query opcional: `?from=YYYY-MM-DD&to=YYYY-MM-DD` para filtrar por rango.

### `GET /api/guardias/raw`
Devuelve el JSON completo (`calendarios.json`) tal cual (para depuración / render multi-mes).

### `GET /api/guardias/stats`
```json
{ "total_meses_con_datos": 10, "total_eventos": 120, "eventos_por_tipo": {"guardia":118,"otro":2},
  "fuentes_csv": 3, "ultima_actualizacion": "2026-07-01T21:02:51" }
```

### `POST /api/guardias`
Crea/asigna una guardia en un día (sobrescribe el día: vacía `eventos` y añade uno).
Body:
```json
{ "fecha": "2026-03-07", "tecnico": "Pilar", "tipo": "guardia", "anotacion": "TARDE" }
```
- Compone `titulo` = `("Media Guardia"|"Guardia") + (" "+anotacion si hay) + " - " + tecnico`.
- Genera `id` = MD5(`fecha_titulo`)[:16]. `origen="manual_edit"`, `all_day=true`, `fecha_edicion=now`.
- Persiste y responde el evento creado.

### `DELETE /api/guardias/:fecha`
Elimina todos los eventos de ese día (solo local). `fecha` = `YYYY-MM-DD`. Persiste.

### `DELETE /api/guardias/mes/:yyyymm`
Borra todos los eventos del mes (solo local). Persiste.

### `POST /api/guardias/bulk`
Guarda una lista de asignaciones (usado por el flujo GPT y opcionalmente por el Generador).
Body:
```json
{ "asignaciones": [ { "fecha":"2026-03-07", "tecnico":"Pilar", "tipo":"guardia" } ],
  "sobrescribirDia": true, "origen": "gpt" }
```
- Para cada asignación válida: si `sobrescribirDia`, vacía el día antes de añadir. Ignora fechas
  inválidas. Responde `{ guardados, ignorados }`.

### `POST /api/guardias/reload`
Fuerza `store.reload()` desde disco. Responde stats.

---

## CSV

### `POST /api/csv/import` (multipart o texto)
Recibe un CSV (fichero) y lo importa (ver reglas en `02-DATA-MODELS §6` y `03 §B.4`).
Responde:
```json
{ "total": 20, "importados": 18, "duplicados": 2, "errores": 0, "errores_detalle": [] }
```

### `POST /api/csv/export`
Body: `{ "asignaciones": [ { "fecha":"2026-03-07","tecnico":"Pilar","tipo":"guardia","titulo":"Guardia - Pilar" } ] }`
- Genera el CSV (formato Google, all-day, agrupando sáb+dom del mismo técnico/tipo).
- Guarda copia en `DATA_DIR/csv/guardias-support.csv`.
- Responde el CSV como texto (`Content-Type: text/csv`, `Content-Disposition: attachment; filename="guardias-support.csv"`).

---

## Google Calendar

### `GET /api/google/status`
```json
{ "configured": true, "authenticated": true,
  "calendar": { "calendar_id": "...", "calendar_name": "Guardias Support", "access_role": "owner" } }
```
`configured` = existe `google_config.json`. `authenticated` = hay token válido.

### `GET /api/google/oauth/login`
Inicia OAuth2: responde `{ "url": "https://accounts.google.com/o/oauth2/..." }` con la URL de
consentimiento (scope `https://www.googleapis.com/auth/calendar`). El frontend abre esa URL.

### `GET /api/google/oauth/callback?code=...`
Callback de Google: intercambia `code` por token, guarda `google_token.json`, y responde una
página simple "Autenticación completada, puedes cerrar esta ventana" (o redirige al frontend).

### `GET /api/google/calendars`
Requiere autenticación. Lista calendarios con permiso de escritura (`owner`/`writer`):
```json
[ { "id":"...", "name":"Guardias Support", "access_role":"owner", "is_primary":false,
    "description":"", "timezone":"Europe/Madrid" } ]
```

### `POST /api/google/config`
Body: `{ "calendar_id":"...", "calendar_name":"...", "access_role":"owner" }`.
Guarda `google_config.json`. Responde el config guardado.

### `POST /api/google/sync/push`  (Local → Google)
Sube todas las guardias del store. Ver algoritmo en `05-GOOGLE-CALENDAR.md`.
Puede ser **streaming de progreso** (SSE) ✨ o una llamada síncrona que devuelve el resumen final:
```json
{ "total": 120, "created": 30, "updated": 90, "errors": 0, "errores_detalle": [],
  "calendar_url": "https://calendar.google.com/calendar/embed?src=..." }
```

### `POST /api/google/sync/pull`  (Google → Local)
Descarga eventos del rango **[hoy−365d, hoy+180d]** y los importa (ver `05`).
```json
{ "total_descargados": 80, "importados_tecnico_activo": 60,
  "importados_tecnico_eliminado": 5, "importados_genericos": 15 }
```

---

## GPT

### `GET /api/gpt/status`
`{ "configured": true, "model": "gpt-4o-mini" }` (`configured` = hay `OPENAI_API_KEY`).

### `GET /api/gpt/reglas-default`
Devuelve el texto de reglas por defecto (constante) para precargar el textarea:
```json
{ "reglas": "REGLAS PARTICULARES:\n\n\nREGLAS GENERALES:\n- ..." }
```

### `POST /api/gpt/generar`
Body:
```json
{ "instrucciones": "<texto del textarea>",
  "fecha_inicio": "2026-10-01", "fecha_fin": "2026-12-31" }
```
El backend:
1. Lee técnicos (orden), festivos dentro del rango, y las **últimas 10 guardias** del store
   (técnico+fecha, más reciente primero).
2. Construye el prompt (ver `06-GPT-INTEGRATION.md`).
3. Llama a OpenAI, parsea el JSON de respuesta.
4. Responde:
```json
{ "asignaciones": [ { "fecha":"2026-10-04","tecnico":"Pilar","tipo":"guardia" } ],
  "prompt_enviado": "..." }
```
Incluir `prompt_enviado` ayuda a depurar (opcional mostrarlo en UI). Errores de OpenAI → `502`/`503`.

---

## Salud

### `GET /api/health` → `{ "ok": true }`
