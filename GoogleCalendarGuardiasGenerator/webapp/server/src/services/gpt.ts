import { config } from "../config";
import { getTecnicoNombres } from "./tecnicos";
import { calendarStore } from "./store";

export const REGLAS_TEXT_DEFAULT = `REGLAS PARTICULARES:


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
- No incluyas comentarios, markdown ni texto fuera del JSON.`;

export function isConfigured(): boolean {
  return !!config.openaiApiKey;
}

export interface UltimaGuardia {
  fecha: string;
  tecnico: string;
}

export function getUltimasGuardias(n = 10): UltimaGuardia[] {
  const eventos = calendarStore
    .getAllEvents()
    .filter((e) => e.tipo === "guardia" && e.tecnico)
    .sort((a, b) => (a.fecha < b.fecha ? 1 : a.fecha > b.fecha ? -1 : 0));

  return eventos.slice(0, n).map((e) => ({ fecha: e.fecha, tecnico: e.tecnico as string }));
}

export function buildPrompt(
  instrucciones: string,
  festivosRango: { fecha: string; anotacion: string }[],
  fechaInicio: string,
  fechaFin: string
): string {
  const tecnicos = getTecnicoNombres();
  const ultimasGuardias = getUltimasGuardias(10);

  const festivosTxt = festivosRango.length
    ? festivosRango
        .slice()
        .sort((a, b) => a.fecha.localeCompare(b.fecha))
        .map((f) => `- ${f.fecha} (${f.anotacion?.trim() || "Festivo"})`)
        .join("\n")
    : "(ninguno)";

  return [
    instrucciones.trim(),
    "",
    `RANGO A ASIGNAR: desde ${fechaInicio} hasta ${fechaFin} (ambos incluidos).`,
    "",
    `TÉCNICOS DISPONIBLES (orden de rotación): ${tecnicos.join(", ")}`,
    "",
    `FESTIVOS EN EL RANGO:\n${festivosTxt}`,
    "",
    `ÚLTIMAS GUARDIAS ASIGNADAS (JSON, de más reciente a más antigua):\n${JSON.stringify(
      ultimasGuardias,
      null,
      2
    )}`
  ].join("\n");
}

export async function generarGuardias(prompt: string): Promise<string> {
  if (!config.openaiApiKey) {
    throw new Error(
      "No se ha encontrado OPENAI_API_KEY. Configúrala en el fichero .env de la raíz de webapp/."
    );
  }

  const { default: OpenAI } = await import("openai");
  const client = new OpenAI({ apiKey: config.openaiApiKey });

  const response = await client.chat.completions.create({
    model: config.openaiModel,
    temperature: 0.2,
    messages: [
      {
        role: "system",
        content:
          "Eres un generador experto de calendarios de guardias de soporte técnico. Debes responder EXCLUSIVAMENTE con el JSON solicitado, sin texto adicional."
      },
      { role: "user", content: prompt }
    ]
  });

  return response.choices[0]?.message?.content || "";
}

export interface AsignacionGpt {
  fecha: string;
  tecnico: string;
  tipo?: "guardia" | "media_guardia";
}

export function parseRespuesta(texto: string): AsignacionGpt[] {
  let jsonText = texto.trim();

  const fenceMatch = jsonText.match(/```(?:json)?\s*(\{[\s\S]*\})\s*```/);
  if (fenceMatch) {
    jsonText = fenceMatch[1];
  } else {
    const braceMatch = jsonText.match(/\{[\s\S]*\}/);
    if (braceMatch) jsonText = braceMatch[0];
  }

  const data = JSON.parse(jsonText);
  if (Array.isArray(data)) return data as AsignacionGpt[];
  return (data.asignaciones as AsignacionGpt[]) || [];
}
