# 03 — Especificación funcional

La app tiene **dos pestañas/páginas** (como la de escritorio): **Generador** y **Visualizador**.
Navegación superior tipo pestañas. La app de escritorio abre por defecto en "Generar Guardias".

Leyenda: 🟢 debe existir (paridad obligatoria) · ✨ mejora web opcional recomendada.

---

## PÁGINA A — Generador de Guardias

Ref: `../desktop/ui/generator_tab.py`.

### A.1 Panel de control (fila superior) 🟢
Cuatro bloques en horizontal:
1. **Último técnico**: desplegable con la lista de técnicos. (En la app actual ya casi no se usa
   porque GPT decide; puedes conservarlo como pista opcional o eliminarlo. Si lo mantienes, que no
   estorbe.)
2. **Período**: dos campos de fecha `Inicio` y `Fin` (formato visible `DD/MM/YYYY`).
   - Valor por defecto de `Inicio`: **día 1 del mes siguiente al actual**.
   - Valor por defecto de `Fin`: **último día de (inicio + 2 meses)** (es decir, un rango de 3 meses).
3. **Tipo de guardia**: radio `Completa` (`guardia`) / `Media` (`media_guardia`).
4. **Técnicos (arrastrables)**: un "chip" por técnico con su color; se arrastran al calendario.

### A.2 Calendario mensual editable 🟢
- Cabecera con navegación `◀`  `Mes Año`  `▶` (navega mes a mes).
- Rejilla semanal Lun→Dom. Fines de semana con fondo distinto (rosado). Festivos con fondo
  distinto (amarillo claro) y etiqueta con la anotación del festivo (o "Festivo").
- **Días asignables**: fines de semana (sáb/dom) y **festivos entre semana** (lunes-viernes).
- **Asignar**: arrastrar un técnico a un día asignable crea la asignación de ese día.
  - Si el día es festivo que cae en fin de semana, pedir confirmación ("¿Asignar guardia de
    fin de semana a X?").
  - El `subject`/título se compone: prefijo (`Guardia` o `Media Guardia`) + anotación de festivo
    si existe + ` - <Tecnico>`. Ej.: `Guardia TARDE - Pilar`.
  - Tipo tomado del selector (A.1.3).
- **Quitar**: click sobre una asignación existente la elimina (solo en memoria de la página).
- Estado de asignaciones vive en la página (no se persiste automáticamente en `calendarios.json`;
  la persistencia ocurre vía **Exportar CSV** o vía el flujo GPT que sí guarda). ✨ Puedes ofrecer
  además un botón "Guardar en local" que escriba directamente en el store por conveniencia, pero
  **mantén** el export CSV.

### A.3 Panel lateral de estadísticas 🟢
- Tabla "Guardias del mes": por técnico → columnas **Técnico**, **Días** (lista de días del mes),
  **Total**.
- **Cálculo del total**: cada día suma `1`, salvo media guardia / guardia TARDE que suma `0.5`.
  (En escritorio se detecta `TARDE` en el título en mayúsculas; replica esa regla, y además
  `tipo == 'media_guardia'` suma 0.5.)
- Colores de fila según color del técnico.

### A.4 Botones de acción 🟢
1. **Crear desde GPT** (antes "Auto-asignar") — abre overlay GPT (ver `06-GPT-INTEGRATION.md`).
   - Valida que `Inicio`/`Fin` sean fechas válidas y `Fin >= Inicio` antes de abrir.
2. **Limpiar** — borra todas las asignaciones de la página (con confirmación).
3. **Exportar CSV** — genera el CSV (formato de `02-DATA-MODELS.md §6`) y lo ofrece como descarga.
   - En escritorio guarda 2 copias (carpeta `csv/` y Escritorio). En web: **descarga del navegador**
     y además POST al backend para guardarlo en `DATA_DIR/csv/guardias-support.csv`. Nombre fijo
     `guardias-support.csv`.

### A.5 Overlay "Crear desde GPT" 🟢
Ref: `../desktop/ui/dialogs/gpt_assign_dialog.py`. **Debe ser un overlay dentro de la app**
(no una ventana/pestaña nueva): capa oscura semitransparente + tarjeta centrada, con botón ✕.
Flujo en dos vistas:

**Vista 1 — Instrucciones**
- Textarea grande **precargado** con el texto de reglas por defecto (ver `06-GPT-INTEGRATION.md`,
  constante `REGLAS_TEXT_DEFAULT`). El usuario edita "REGLAS PARTICULARES".
- Muestra el rango a asignar (de A.1.2).
- Botón **Enviar a GPT** (deshabilita y muestra "Generando…"), botón **Cancelar**.
- Si no hay `OPENAI_API_KEY`, mostrar error claro.

**Vista 2 — Revisión**
- Tabla con la propuesta devuelta por GPT: columnas **Fecha**, **Técnico**, **Tipo**, ordenada por fecha.
- Botón **Guardar en calendario local** → escribe cada asignación en `calendarios.json` vía backend
  (sobrescribiendo el día: vaciar `eventos` del día antes de añadir). Al terminar, mensaje indicando
  cuántas se guardaron y recordando ir al Visualizador a pulsar "Sincro: Local → Google".
- Botón **Descartar** cierra sin guardar.
- Si GPT no devuelve asignaciones, mostrar aviso y permitir cerrar.

---

## PÁGINA B — Visualizador de Calendarios

Ref: `../desktop/ui/viewer_tab.py` + `../desktop/ui/components/multi_month_viewer.py`.

### B.1 Barra de herramientas 🟢
Distribución (según último estado de la app de escritorio):
- **Izquierda**: etiqueta `Calendario seleccionado: <nombre o "No configurado">` + botón **Login/config**
  (sin icono) que abre el modal de configuración de Google (ver `05-GOOGLE-CALENDAR.md`).
- **Centro** (grupo centrado): botones
  1. **Importar CSV** — sube un CSV y lo importa al store (ver reglas import en `02 §6` y B.4).
  2. **Actualizar** — recarga datos desde disco (store.reload) y repinta, volviendo al mes actual.
  3. **Sincro: Local → Google** — sube todas las guardias locales a Google (push). *Deshabilitado si
     no hay calendario configurado.*
  4. **Sincro: Google → Local** — descarga eventos de Google al store (pull). *Deshabilitado si no
     hay calendario configurado.*

### B.2 Vista multi-mes 🟢
- Muestra **7 meses** a la vez por defecto (equivalente a `num_months=7`). ✨ En web puedes hacerlo
  responsive (grid que se adapte), pero por defecto ~7 meses visibles con scroll.
- Navegación: `◀◀ -1 Año`, `◀ -1 Mes`, `HOY`, `► +1 Mes`, `►► +1 Año`.
- Cada mes: rejilla Lun→Dom; fines de semana con fondo distinto; cada día muestra hasta ~2 eventos
  (nombre del técnico) con el color del técnico; si hay más, "+N más".
- **Edición desde el visor** (como en escritorio):
  - Arrastrar un técnico (paleta de técnicos en la barra de navegación del visor) a un día → asigna
    (crea evento `Guardia - <Tecnico>`, `tipo guardia`, `origen manual_edit`), **sobrescribiendo** el
    día (vacía eventos previos), y **persiste en el store** inmediatamente. **No** toca Google.
  - Click sobre una guardia → la elimina **solo en local** (persiste el borrado en el store).
    **No** toca Google. (Este comportamiento es importante: editar/borrar en local NUNCA modifica
    Google hasta pulsar el botón de sincronización explícito.)
  - ✨ Menú/gesto para "borrar todas las guardias del mes" (existe en escritorio como
    `_delete_month_events`, solo-local, con confirmación).

### B.3 Panel de estadísticas por mes 🟢
- Por cada mes, panel lateral "Técnicos" con Técnico / Días / Total (misma regla de 0.5 para TARDE).
- **Técnico eliminado** (💀): si un evento tiene un `tecnico` que **ya no existe** en `tecnicos.txt`,
  se muestra con **fondo negro, texto blanco y un emoji 💀 delante del nombre**, tanto en la celda
  del día como en la tabla de estadísticas. (Ref: `_tecnico_style` en `multi_month_viewer.py`.)

### B.4 Importar CSV 🟢
- Selección de fichero → parse → importar al store.
- Detección de duplicado de fichero por **hash MD5** (si ya se importó ese fichero, no reimporta).
- Al importar, si un día ya tiene técnico asignado, **no** se sobrescribe (se cuenta como duplicado).
- Devuelve estadísticas: `total`, `importados`, `duplicados`, `errores` (+ detalle primeras filas).

### B.5 Barra de estado 🟢
- Texto: `Total eventos: N | Meses: M | Última actualización: <fecha> | Google: <nombre|No configurado>`.

---

## Sincronización con Google (resumen; detalle en 05)

- **Local → Google** (`sync push`): sube TODAS las guardias del store. Crea o actualiza; evita
  duplicados buscando por fecha+título si el evento no tiene `google_event_id`. Guarda el
  `google_event_id`/`google_link` devuelto en el store. Muestra resumen (total, creados,
  actualizados, errores) y enlace al calendario.
- **Google → Local** (`sync pull`): descarga eventos del calendario configurado en un rango fijo de
  **12 meses hacia atrás y 6 meses hacia delante** desde hoy. Importa **tal cual** (sin preguntar):
  - Si el título casa el patrón `^Guardia\s*-\s*(.+)$`, usa ese técnico y `tipo=guardia`
    (aunque el técnico ya no exista → se marcará con 💀 en la vista).
  - Si no casa el patrón, importa como `tecnico=null`, `tipo=otro`.
  - Sobrescribe/añade respetando duplicados por `id`.
  - Muestra resumen: total descargados, importados (técnico activo), importados (técnico ya no
    existe 💀), importados (genéricos).
- **Regla crítica**: la edición/borrado local NUNCA modifica Google automáticamente. Solo los
  botones de sincronización explícitos mueven datos entre local y Google.

---

## Comportamientos que NO deben perderse (checklist de paridad)

- [ ] Colores por técnico desde `tecnicos.txt`, en orden.
- [ ] Festivos con anotación; TARDE = 0.5 en estadísticas.
- [ ] Días asignables = findes + festivos entre semana.
- [ ] Título compuesto con anotación de festivo.
- [ ] Un evento por día (sobrescritura al reasignar).
- [ ] Export CSV all-day con End Date exclusivo y agrupación sáb+dom.
- [ ] Import CSV con dedupe por hash y por día ya ocupado.
- [ ] `id` = MD5(`fecha_titulo`)[:16].
- [ ] Crear desde GPT: overlay, reglas por defecto, revisión previa, guardado en local.
- [ ] Multi-mes (7), navegación, estadísticas, marca 💀 de técnico eliminado.
- [ ] Login/config Google + etiqueta de calendario seleccionado.
- [ ] Sync push (local→Google) y pull (Google→local, rango −12/+6 meses).
- [ ] Edición/borrado local nunca toca Google.
- [ ] Barra de estado con métricas + estado de Google.
