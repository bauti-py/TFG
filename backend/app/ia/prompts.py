import json
from app.ia import toon


def _serializar(payload: dict) -> tuple[str, int]:
    bloque = toon.codificar(payload)
    json_equivalente = toon.estimar_tokens(json.dumps(payload, ensure_ascii=False))
    return bloque, json_equivalente


def prompt_asignacion(tarea: dict, desarrolladores: list[dict]) -> tuple[str, int]:
    bloque, json_equivalente = _serializar({"tarea": tarea, "desarrolladores": desarrolladores})
    prompt = f"""Sos un asistente de gestión de equipos de desarrollo de software.
Primero INFERÍ las habilidades técnicas que requiere la tarea a partir de su descripción
(si "habilidades_requeridas" viene vacío, deducilas vos del texto: lenguajes, frameworks y
dominios involucrados). Luego seleccioná al Desarrollador con MEJOR AJUSTE, cruzando esas
habilidades con el perfil de conocimiento (lenguajes, dominios, frameworks, seniority), la
carga de trabajo actual (menor carga es preferible si el perfil ajusta) y el historial de
tareas similares.

Datos (notación TOON):
{bloque}

Respondé EXCLUSIVAMENTE con un objeto JSON válido con esta forma:
{{"id_usuario_asignado": <id o null>, "confianza": <0.0-1.0>, "motivo": "<breve justificación>", "habilidades_inferidas": ["<lenguaje/framework/dominio>", ...]}}
"habilidades_inferidas" son las que dedujiste de la descripción (en minúscula, ej: "python", "react", "backend").
Si ningún desarrollador tiene ajuste suficiente, devolvé "id_usuario_asignado": null."""
    return prompt, json_equivalente


def prompt_consulta_avance(
    tarea: dict, desarrollador: dict, historial: list[dict] | None = None
) -> tuple[str, int]:
    bloque, json_equivalente = _serializar(
        {"tarea": tarea, "desarrollador": desarrollador, "historial": historial or []}
    )
    prompt = f"""Sos un asistente que hace seguimiento asincrónico del avance de tareas,
reemplazando la reunión diaria. Generá UNA sola pregunta breve, cordial y concreta
para consultarle al Desarrollador cómo va su tarea. No saludes en exceso.

Usá el HISTORIAL de preguntas y respuestas previas (si lo hay): profundizá en lo ÚLTIMO
que respondió el desarrollador y hacé una pregunta NUEVA y MÁS ESPECÍFICA que avance la
conversación. NO repitas preguntas ya hechas. Si no hay historial, hacé una pregunta
inicial abierta sobre el avance de la tarea.

Contexto (notación TOON):
{bloque}

Respondé solo con el texto de la pregunta, sin comillas ni prefijos."""
    return prompt, json_equivalente


def prompt_inferir_estado(
    tarea: dict, respuesta_desarrollador: str, historial: list[dict] | None = None
) -> tuple[str, int]:
    bloque, json_equivalente = _serializar(
        {
            "tarea": tarea,
            "historial": historial or [],
            "respuesta_desarrollador": respuesta_desarrollador,
        }
    )
    prompt = f"""Analizá la ÚLTIMA respuesta de un Desarrollador sobre el avance de su tarea
e inferí el estado actual. Tené en cuenta TODO el historial de la conversación: el
desarrollador puede referirse a mensajes anteriores (por ejemplo preguntar si ya se le
resolvió un bloqueo). No marques BLOQUEADA si la última respuesta indica que ya avanza o
que el impedimento se resolvió.

Estados posibles:
- EN_PROGRESO: está trabajando, hay avance, sin impedimentos.
- BLOQUEADA: hay un impedimento que frena el avance.
- COMPLETADA: la tarea está terminada.

Datos (notación TOON):
{bloque}

Respondé EXCLUSIVAMENTE con JSON:
{{"estado": "EN_PROGRESO|BLOQUEADA|COMPLETADA", "resumen": "<síntesis del avance>", "contexto_bloqueo": "<si BLOQUEADA, describí el impedimento; si no, null>"}}"""
    return prompt, json_equivalente


def prompt_resumen(tarea: dict, historial: list[dict]) -> tuple[str, int]:
    bloque, json_equivalente = _serializar({"tarea": tarea, "historial": historial})
    prompt = f"""Sos un asistente que informa al Scrum Master y al Líder Técnico. Resumí en
2 o 3 frases el estado de avance de esta tarea según la conversación del desarrollador con
el asistente: qué avanzó, si hay impedimentos y si quedó completada. Concreto y breve.

Datos (notación TOON):
{bloque}

Respondé solo con el texto del resumen, sin prefijos ni comillas."""
    return prompt, json_equivalente
