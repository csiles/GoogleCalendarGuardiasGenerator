# 06 — Integración con GPT (OpenAI)

Referencia Python: `../desktop/utils/gpt_assign.py`. Replica con el paquete Node **`openai`**.

## Configuración
- `OPENAI_API_KEY` en `.env` (obligatoria).
- `OPENAI_MODEL` (por defecto `gpt-4o-mini`).
- `is_configured()` = existe `OPENAI_API_KEY`.

## Constante `REGLAS_TEXT_DEFAULT` (texto exacto a precargar en el textarea)

Copia **literalmente** este texto (respeta saltos de línea; las "REGLAS PARTICULARES" quedan vacías
para que el usuario las rellene). Exponlo vía `GET /api/gpt/reglas-default`.

```text
REGLAS PARTICULARES:


REGLAS GENERALES:
- Las guardias son de fin de semana completo (sábado y domingo).
- En caso de festivo entre semana:
  - Si cae en lunes, la guardia la cubre el técnico que hizo el fin de semana inmediatamente anterior.
  - Si cae de martes a viernes, la guardia la cubre el técnico que hará el fin de semana siguiente.
  - Si se forma un bloque de 4 días seguidos (por ejemplo jueves-viernes-sábado-domingo, o viernes-sábado-domingo-lunes), el bloque se divide en dos: un técnico cubre los dos primeros días y otro técnico los dos últimos.
- Si un técnico tiene vacaciones, no puede tener guardia ni el fin de semana en el que sale de vacaciones ni el fin de semana en el que se reincorpora. Es decir, si su último día laboral antes de vacaciones es un viernes, no puede tener guardia ese fin de semana; y si se reincorpora un lunes, no puede tener guardia el fin de semana inmediatamente anterior.
- Los técnicos rotan siempre en el mismo orden en el que aparecen en la lista de técnicos proporcionada.
- Para elegir el primer técnico al que asignar las nuevas guardias, evalúa el orden de rotación y quiénes hicieron las últimas guardias facilitadas, de forma que no se repita un técnico mientras haya otros que todavía no la hayan hecho.

FORMATO DE RESPUESTA (obligatorio):
Responde ÚNICAMENTE con un bloque JSON válido, sin texto ni explicaciones antes o después, con esta estructura exacta:
{
  "asignaciones": [
    { "fecha": "YYYY-MM-DD", "tecnico": "Nombre del técnico", "tipo": "guardia" }
  ]
}
- "fecha" en formato ISO (YYYY-MM-DD).
- "tecnico" debe ser exactamente uno de los nombres de la lista de técnicos proporcionada.
- "tipo" debe ser "guardia" (día completo) o "media_guardia" (medio día), según corresponda.
- Incluye una entrada por cada día de guardia (sábado y domingo por separado, aunque sea el mismo técnico).
- No incluyas comentarios, markdown ni texto fuera del JSON.
```

## Construcción del prompt (`build_prompt`)

El backend concatena, en este orden, separando bloques con líneas en blanco:

1. `instrucciones.trim()` (el texto del textarea, ya incluye las reglas de arriba editadas).
2. `RANGO A ASIGNAR: desde <inicio YYYY-MM-DD> hasta <fin YYYY-MM-DD> (ambos incluidos).`
3. `TÉCNICOS DISPONIBLES (orden de rotación): <n1, n2, ...>`
4. `FESTIVOS EN EL RANGO:` seguido de líneas `- YYYY-MM-DD (<anotacion|Festivo>)`, o `(ninguno)`.
5. `ÚLTIMAS GUARDIAS ASIGNADAS (JSON, de más reciente a más antigua):` seguido del JSON
   (indent 2, UTF-8) de las **10 últimas** guardias: `[{ "fecha":"YYYY-MM-DD", "tecnico":"..." }]`.

Las "últimas guardias" se obtienen del store: eventos con `tipo == 'guardia'` y `tecnico` no vacío,
ordenados por `fecha` **descendente**, tomando 10.

## Llamada a OpenAI

- `chat.completions.create` con:
  - `model` = `OPENAI_MODEL`.
  - `temperature: 0.2`.
  - `messages`:
    - system: `"Eres un generador experto de calendarios de guardias de soporte técnico. Debes responder EXCLUSIVAMENTE con el JSON solicitado, sin texto adicional."`
    - user: `<prompt construido>`.
- ✨ Recomendado en web: añade `response_format: { type: 'json_object' }` para forzar JSON válido
  (mejora sobre la app de escritorio). El parsing debe seguir siendo tolerante igualmente.

## Parsing de la respuesta (`parse_respuesta`)

Tolerante a que el modelo envuelva el JSON:
1. Si hay bloque markdown ```json ... ``` extrae su interior.
2. Si no, busca el primer `{ ... }` que abarque todo (regex `\{.*\}` con dotall).
3. `JSON.parse`. Si es array, devuélvelo; si es objeto, devuelve `data.asignaciones ?? []`.
4. Cada asignación válida: `{ fecha: 'YYYY-MM-DD', tecnico: string, tipo: 'guardia'|'media_guardia' }`.
   Ignora entradas sin `fecha`/`tecnico` o con fecha no parseable.

## Guardado tras revisión

Cuando el usuario acepta en la vista de revisión (overlay), se llama a
`POST /api/guardias/bulk` con `{ asignaciones, sobrescribirDia: true, origen: 'gpt' }`.
El título de cada evento se compone como `("Media Guardia"|"Guardia") + " - " + tecnico`
(el flujo GPT del escritorio no añade anotación de festivo al título; mantenlo así).
