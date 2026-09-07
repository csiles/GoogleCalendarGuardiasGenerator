# 02 — Modelos de datos

Todos los formatos deben ser **compatibles con la app de escritorio** (`../desktop/`).
Respeta nombres de campos y semántica EXACTAMENTE.

---

## 1. `tecnicos.txt`

Texto plano, una línea por técnico, **el orden importa** (es el orden de rotación):

```
Nombre,#RRGGBB
```

Ejemplo real:
```
Pilar,#3498db
Isa,#e74c3c
Romane,#2ecc71
Yannick,#f39c12
Mayra,#9b59b6
Raquel,#1abc9c
```

Reglas de parseo (ver `../desktop/utils/file_utils.py`):
- Ignora líneas vacías.
- Separador `,`. Primer campo = nombre (trim). Segundo = color hex.
- Si no hay color, usar `#3498db` por defecto.
- API expone: `[{ "nombre": "Pilar", "color": "#3498db" }, ...]` **en orden**.

---

## 2. `festivos.txt`

Texto plano, una línea por festivo:

```
DD/MM/YYYY, ANOTACION_OPCIONAL
```

Ejemplo real (ojo: el fichero real tiene inconsistencias como `.` en vez de `,`; sé tolerante):
```
18/03/2026, TARDE
19/03/2026,
03/04/2026,
06/04/2026,
01/05/2026.
25/12/2026
```

Reglas de parseo (ver `../desktop/utils/file_utils.py`):
- Ignora líneas vacías.
- Separa por `,`. Primer campo = fecha `DD/MM/YYYY`. Resto = anotación (trim, puede estar vacía).
- Fechas inválidas se ignoran (log de aviso).
- La anotación `TARDE` es relevante: indica media guardia / guardia de tarde (afecta a estadísticas: suma 0.5 en vez de 1, ver `03-FUNCTIONAL-SPEC.md`).
- API expone: `[{ "fecha": "2026-03-18", "anotacion": "TARDE" }, ...]` (fecha normalizada a ISO `YYYY-MM-DD`).

---

## 3. `calendarios.json` (almacén principal de guardias)

Estructura (ver `../desktop/models/calendar_manager.py`):

```json
{
  "version": "1.0",
  "last_updated": "2026-07-01T21:02:51.051017",
  "meses": {
    "2026-03": {
      "dias": {
        "07": {
          "eventos": [
            {
              "id": "4fc51a7b5299c8d3",
              "titulo": "Guardia - Pilar",
              "tecnico": "Pilar",
              "tipo": "guardia",
              "descripcion": "",
              "all_day": true,
              "origen": "manual_edit",
              "fecha_edicion": "2026-07-01T21:02:51.051017"
            }
          ]
        }
      },
      "estadisticas_mes": {
        "total_eventos": 1,
        "por_tipo": { "guardia": 1 }
      }
    }
  },
  "fuentes_csv": [
    {
      "nombre": "guardias-support.csv",
      "ruta": "...",
      "fecha_carga": "2026-...",
      "registros_importados": 12,
      "hash": "md5hex"
    }
  ]
}
```

Detalles clave:
- **Claves de mes**: `"YYYY-MM"`. **Claves de día**: `"DD"` (con cero a la izquierda).
- Cada día tiene `eventos: []`. En la práctica **un día tiene 0 o 1 evento** (al asignar se
  vacía el array antes de añadir; ver "sobrescritura" en spec).
- Campos de un evento:
  - `id`: string. Se genera como **MD5 de `f"{fecha}_{titulo}"`, primeros 16 hex chars**.
    (Python: `hashlib.md5(f"{fecha}_{titulo}".encode()).hexdigest()[:16]`). Replica esto en Node con `crypto`.
  - `titulo`: `"Guardia - <Tecnico>"` o `"Media Guardia - <Tecnico>"`. También puede venir con
    anotación de festivo: `"Guardia TARDE - <Tecnico>"` según el generador (ver export CSV).
  - `tecnico`: nombre del técnico (o `null` si el evento vino de Google sin patrón reconocible).
  - `tipo`: `"guardia"` | `"media_guardia"` | `"otro"`.
  - `descripcion`: string (por defecto `""`).
  - `all_day`: bool (normalmente `true`).
  - `origen`: `"manual_edit"` | `"csv_import"` | `"google_pull"` | `"gpt"`.
  - Campos opcionales según origen: `fecha_edicion`, `fecha_importacion`, `archivo_origen`,
    `google_event_id`, `google_link`.
- `estadisticas_mes`: se recalcula al añadir. `total_eventos` (int) y `por_tipo` (map tipo→count).
  Puedes recalcularlo íntegro al escribir para evitar desincronización.
- `fuentes_csv`: registro de CSV importados con su hash MD5 (para evitar reimportar el mismo fichero).

### Estructura vacía inicial
```json
{ "version": "1.0", "last_updated": "<ISO now>", "meses": {}, "fuentes_csv": [] }
```

### Operaciones del store (equiv. `CalendarManager`)
- `load()` / `reload()`: leer del disco; si falta o está corrupto o le faltan `meses`/`fuentes_csv`, devolver estructura vacía.
- `save()`: actualizar `last_updated` (ISO) y escribir con indent 2, `ensure_ascii=false` (UTF-8).
- `addEvent(fecha, evento)`: crea mes/día si faltan; **evita duplicados por `id`** (si el `id` ya existe en el día, no añade y devuelve false); actualiza estadísticas.
- `getAllEvents()`: aplana todos los eventos añadiendo `fecha: "YYYY-MM-DD"` a cada uno.
- `getStatistics()`: `{ total_meses_con_datos, total_eventos, eventos_por_tipo, fuentes_csv, ultima_actualizacion }`.
- `updateGoogleEventId(fecha, id, google_event_id, google_link)`: setea esos campos en el evento.

---

## 4. `google_config.json`

Se genera al elegir calendario (ver `../desktop/utils/google_calendar_sync.py`):

```json
{
  "calendar_id": "c_xxxx@group.calendar.google.com",
  "calendar_name": "Guardias Support",
  "access_role": "owner",
  "configured_at": "2026-05-12T08:34:03.012582"
}
```

---

## 5. `google_credentials.json` y `google_token.json`

- `google_credentials.json`: fichero de credenciales OAuth "Desktop/Web app" descargado de
  Google Cloud Console. **Secreto, no versionar.** Lo aporta el usuario.
- `google_token.json`: token de acceso/refresh generado tras el primer login OAuth. **Secreto.**

---

## 6. CSV de guardias (formato Google Calendar import/export)

Cabecera EXACTA (ver `../desktop/ui/generator_tab.py::_export_csv` y `CalendarManager.import_csv`):

```
Subject,Start Date,Start Time,End Date,End Time,All Day Event,Description,Location,Private
```

- `Subject`: `"Guardia - <Tecnico>"` (o con anotación / "Media Guardia").
- `Start Date`, `End Date`: `YYYY-MM-DD`.
- `Start Time`, `End Time`: `00:00:00`.
- `All Day Event`: `True`.
- **Importante (all-day)**: `End Date` es **exclusivo** = día siguiente al último día real del evento.
  Al **exportar**, si un técnico tiene sábado+domingo seguidos, se agrupa en un único evento
  `Start=sábado`, `End=lunes` (domingo+1). Al **importar**, para all-day se recorre desde
  `Start Date` hasta `End Date - 1 día` creando un evento por día.
- Al importar, el técnico se extrae del `Subject` tomando el texto tras el último `" - "`.
- `Description`, `Location`, `Private` pueden ir vacíos / `False`.
