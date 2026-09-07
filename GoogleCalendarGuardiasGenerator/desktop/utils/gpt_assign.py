"""
Integración con OpenAI (GPT) para generar propuestas de asignación de guardias.
"""

import os
import re
import json
import logging
from datetime import date
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

ENV_FILE = ".env"

# Texto por defecto que se muestra (y puede editarse) en el modal "Crear desde GPT".
# Las secciones de técnicos, festivos, rango de fechas y últimas guardias se añaden
# automáticamente al final justo antes de enviarlo a GPT.
REGLAS_TEXT_DEFAULT = """REGLAS PARTICULARES:


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
- No incluyas comentarios, markdown ni texto fuera del JSON."""


def _load_env_file(path: str = ENV_FILE) -> None:
    """Carga variables de entorno desde un fichero .env simple (KEY=VALUE por línea)"""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


_load_env_file()

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def is_configured() -> bool:
    """Comprueba si hay una API key de OpenAI disponible"""
    return bool(os.environ.get("OPENAI_API_KEY"))


def build_prompt(instrucciones: str, tecnicos: List[str], festivos_rango: Dict[date, str],
                  ultimas_guardias: List[dict], fecha_inicio: date, fecha_fin: date) -> str:
    """Construye el prompt final a enviar a GPT combinando las instrucciones editables
    con el contexto dinámico (técnicos, festivos, rango y últimas guardias)"""
    if festivos_rango:
        festivos_txt = "\n".join(
            f"- {fecha.strftime('%Y-%m-%d')} ({motivo.strip() if motivo and motivo.strip() else 'Festivo'})"
            for fecha, motivo in sorted(festivos_rango.items())
        )
    else:
        festivos_txt = "(ninguno)"

    partes = [
        instrucciones.strip(),
        "",
        f"RANGO A ASIGNAR: desde {fecha_inicio.strftime('%Y-%m-%d')} hasta {fecha_fin.strftime('%Y-%m-%d')} (ambos incluidos).",
        "",
        f"TÉCNICOS DISPONIBLES (orden de rotación): {', '.join(tecnicos)}",
        "",
        f"FESTIVOS EN EL RANGO:\n{festivos_txt}",
        "",
        f"ÚLTIMAS GUARDIAS ASIGNADAS (JSON, de más reciente a más antigua):\n"
        f"{json.dumps(ultimas_guardias, ensure_ascii=False, indent=2)}"
    ]
    return "\n".join(partes)


def generar_guardias(prompt: str, model: Optional[str] = None) -> str:
    """Envía el prompt a GPT y devuelve el texto de la respuesta"""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se ha encontrado OPENAI_API_KEY. Configúrala en el fichero .env de la raíz del proyecto."
        )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un generador experto de calendarios de guardias de soporte técnico. "
                    "Debes responder EXCLUSIVAMENTE con el JSON solicitado, sin texto adicional."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


def parse_respuesta(texto: str) -> List[dict]:
    """Extrae la lista de asignaciones del JSON devuelto por GPT, tolerando bloques markdown"""
    texto = texto.strip()

    # Quitar vallas de código markdown si las hay
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texto, re.DOTALL)
    if fence_match:
        texto = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", texto, re.DOTALL)
        if brace_match:
            texto = brace_match.group(0)

    data = json.loads(texto)

    if isinstance(data, list):
        return data
    return data.get("asignaciones", [])
