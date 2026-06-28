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
    prompt = f"""Sos un asistente que hace seguimiento asincrónico del avance de tareas (reemplaza
la daily). Analizá la ÚLTIMA respuesta del Desarrollador EN EL CONTEXTO de TODA la conversación e
inferí: (1) el estado actual de la tarea y (2) si conviene seguir conversando o cerrar la charla.

Leé el historial completo: el desarrollador puede referirse a mensajes anteriores (por ejemplo
preguntar si ya le resolvieron un bloqueo).

Estados:
- EN_PROGRESO: está trabajando, hay avance. Es el estado POR DEFECTO.
- BLOQUEADA: úsalo SOLO si el desarrollador dice EXPLÍCITAMENTE que está FRENADO y NO puede
  avanzar por su cuenta, y necesita ayuda de otra persona o un recurso/permiso que no tiene
  (ej.: "estoy trabado y no puedo seguir hasta que me den acceso", "necesito que el SM me
  habilite X"). Que sea un BLOQUEO REAL que requiera escalarlo.
- COMPLETADA: la tarea está terminada.

MUY IMPORTANTE — no sobre-detectes bloqueos:
- Mencionar un tema, bug, duda o pendiente que el desarrollador ESTÁ investigando o resolviendo
  por su cuenta NO es un bloqueo. Ej.: "vengo viendo un tema de las api keys", "estoy revisando
  un bug", "ajustando unos detalles" → eso es EN_PROGRESO, sigue avanzando.
- Palabras como "tema", "problema", "viendo", "revisando" NO implican BLOQUEADA por sí solas.
- Si NO afirma claramente que está frenado y que necesita ayuda externa, es EN_PROGRESO.
- NO marques BLOQUEADA si ya avanza o si el impedimento se resolvió.
- Ante la duda, EN_PROGRESO: un falso bloqueo genera escalamientos y ruido innecesario.

Campo "continuar" (clave: NO seas insistente, respetá al desarrollador):
- false si el desarrollador DA POR TERMINADA la charla o no hay nada útil para preguntar ahora.
  Señales de cierre: "nada más", "eso es todo", "después te cuento", "luego sigo", "listo por hoy",
  "por ahora nada", "gracias", "ok", "dale", o una respuesta corta de mera cortesía. Ante la duda,
  si suena a cierre cordial, poné false: NO vuelvas a preguntar.
- true SOLO si la respuesta deja algo concreto y abierto para profundizar y el desarrollador
  claramente sigue en la conversación.
Si el estado es COMPLETADA o BLOQUEADA, "continuar" debe ser false (no hay que seguir indagando).

Datos (notación TOON):
{bloque}

Respondé EXCLUSIVAMENTE con JSON:
{{"estado": "EN_PROGRESO|BLOQUEADA|COMPLETADA", "continuar": true|false, "resumen": "<síntesis del avance>", "contexto_bloqueo": "<si BLOQUEADA, el impedimento; si no, null>", "cierre": "<si continuar=false, UNA frase breve y cordial para cerrar acorde al contexto; si no, null>"}}"""
    return prompt, json_equivalente


def prompt_resumen_actividad_dev(desarrollador: dict, tareas: list[dict]) -> tuple[str, int]:
    bloque, json_equivalente = _serializar({"desarrollador": desarrollador, "tareas": tareas})
    prompt = f"""Sos un asistente que le arma al Scrum Master un seguimiento del avance de UN
desarrollador. Con las tareas del sprint asignadas a esta persona (cada una con su estado, sus
fechas y la conversación de avance que tuvo con el asistente), escribí un RESUMEN NARRATIVO,
claro y concreto, contando qué viene haciendo. En español rioplatense, tono profesional.

Cubrí, cuando los datos lo permitan:
- Por cada tarea que arrancó: cuándo la empezó (fecha de inicio) y qué fue avanzando según la
  conversación (pasos concretos, decisiones, lo que mencionó).
- En qué está trabajando ACTUALMENTE y el estado de cada tarea (en progreso, bloqueada, completada).
- Si hay tareas asignadas que TODAVÍA NO arrancó, mencionalo.
- Si alguna está bloqueada, decí por qué.

Reglas:
- Usá SOLO la información de los datos. No inventes avances que no estén en las conversaciones.
- Si una tarea no tiene conversación, decí que aún no hay reportes de avance de esa tarea.
- 1 o 2 párrafos breves. Sin viñetas ni encabezados, redacción corrida.

Datos (notación TOON):
{bloque}

Respondé solo con el texto del resumen, sin prefijos ni comillas."""
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
