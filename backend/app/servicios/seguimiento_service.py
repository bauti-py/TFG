"""Seguimiento conversacional asincrónico (CU4, RF6/RF7/RF12)."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.esquemas.seguimiento import ConsultaAvanceSalida, ResultadoSeguimiento
from app.ia import cliente_gemini, prompts
from app.modelos.enums import EstadoTarea
from app.modelos.tarea import Tarea
from app.repositorios import conversacion_repo, perfil_repo
from app.servicios import bloqueo_service, estado_service
from app.servicios.usuario_service import obtener_por_id


_PISTAS_DESTRABE = (
    "ya me lo resolv", "ya lo resolv", "se resolvi", "se solucion", "destrab", "pude seguir",
    "pude avanzar", "pude continuar", "ya pude", "ahora sí", "ahora si", "ya tengo acceso",
    "ya me cargaste", "ya me dieron", "quedó destrabado",
)
_PISTAS_COMPLETA = (
    "termin", "complet", "finalic", "finaliz", "ya está list", "ya esta list", "quedó listo",
    "quedo listo", "ya lo hice", "hecho", "mergeado", "lo deployé", "lo deploye",
)
_PISTAS_BLOQUEO = (
    "trabé", "trabe", "trabó", "trabado", "trabada", "atasc", "atorad", "bloque", "impedimento",
    "no puedo avanzar", "no me deja", "no me anda", "no funciona", "no tengo acceso",
    "no tengo las", "me falta", "necesito ayuda", "necesito que", "esperando", "depende de",
    "frenad", "no pude",
)


def _inferir_determinista(texto: str) -> dict:
    """Inferencia por palabras clave cuando la IA no respondió. Mantiene el Q&A vivo."""
    t = texto.lower()
    if any(p in t for p in _PISTAS_DESTRABE):
        return {"estado": "EN_PROGRESO", "resumen": "¡Genial que se haya destrabado! Seguí avanzando.", "contexto_bloqueo": None}
    if any(p in t for p in _PISTAS_COMPLETA):
        return {"estado": "COMPLETADA", "resumen": "¡Genial! Marco la tarea como completada.", "contexto_bloqueo": None}
    if any(p in t for p in _PISTAS_BLOQUEO):
        return {
            "estado": "BLOQUEADA",
            "resumen": "Detecté un posible bloqueo en tu respuesta; avisé al Scrum Master.",
            "contexto_bloqueo": texto,
        }
    return {"estado": "EN_PROGRESO", "resumen": "Anotado, seguís en progreso. ¡Gracias por el update!", "contexto_bloqueo": None}


async def _tarea_payload(db: AsyncSession, tarea: Tarea) -> dict:
    estado = await estado_service.estado_actual(db, tarea.id_tarea)
    return {
        "id": tarea.id_tarea,
        "descripcion": tarea.descripcion,
        "estado_actual": estado.value,
        "habilidades": [h.strip() for h in (tarea.habilidades_requeridas or "").split(",") if h.strip()],
    }


async def generar_consulta(db: AsyncSession, tarea: Tarea) -> ConsultaAvanceSalida:
    if tarea.id_usuario_asignado is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La tarea no tiene desarrollador asignado")

    dev = await obtener_por_id(db, tarea.id_usuario_asignado)
    perfil = await perfil_repo.obtener_perfil(tarea.id_usuario_asignado) or {}
    dev_payload = {"nombre": dev.nombre if dev else "", "seniority": perfil.get("seniority", "N/D")}

    historial = await _historial(tarea.id_tarea)

    prompt, json_equivalente = prompts.prompt_consulta_avance(
        await _tarea_payload(db, tarea), dev_payload, historial
    )
    pregunta = await cliente_gemini.generar(
        tipo="consulta_avance", prompt=prompt, id_usuario=tarea.id_usuario_asignado,
        id_tarea=tarea.id_tarea, tokens_json_equivalente=json_equivalente,
    )
    if pregunta is None:
        pregunta = (
            "¿Algún avance nuevo desde la última actualización? ¿Seguís con algún bloqueo?"
            if historial
            else f"¡Hola{(' ' + dev.nombre.split()[0]) if dev else ''}! ¿Cómo venís con «{tarea.descripcion}»?"
        )
    pregunta = pregunta.strip()

    await conversacion_repo.agregar_consulta(tarea.id_tarea, tarea.id_usuario_asignado, pregunta)
    return ConsultaAvanceSalida(id_tarea=tarea.id_tarea, pregunta=pregunta)


async def _historial(id_tarea: int) -> list[dict]:
    """Pares pregunta/respuesta previos de la conversación (contexto para la IA)."""
    return [
        {"pregunta": c["consulta"]["texto"], "respuesta": (c.get("respuesta") or {}).get("texto")}
        for c in await conversacion_repo.listar_por_tarea(id_tarea)
        if c.get("consulta")
    ]


async def resumir_conversacion(db: AsyncSession, tarea: Tarea) -> str:
    historial = await _historial(tarea.id_tarea)
    if not historial:
        return "Todavía no hay conversación de avance para esta tarea."

    prompt, json_equivalente = prompts.prompt_resumen(await _tarea_payload(db, tarea), historial)
    resumen = await cliente_gemini.generar(
        tipo="resumen_seguimiento", prompt=prompt, id_usuario=tarea.id_usuario_asignado,
        id_tarea=tarea.id_tarea, tokens_json_equivalente=json_equivalente,
    )
    if resumen is None:
        estado = await estado_service.estado_actual(db, tarea.id_tarea)
        respuestas = [h["respuesta"] for h in historial if h.get("respuesta")]
        ultimo = respuestas[-1] if respuestas else "sin respuestas todavía"
        return (
            f"Estado actual: {estado.value.replace('_', ' ').lower()}. "
            f"{len(respuestas)} respuesta(s) del desarrollador. Último: «{ultimo}»."
        )
    return resumen.strip()


async def procesar_respuesta(db: AsyncSession, tarea: Tarea, texto: str) -> ResultadoSeguimiento:
    prompt, json_equivalente = prompts.prompt_inferir_estado(
        await _tarea_payload(db, tarea), texto, await _historial(tarea.id_tarea)
    )
    inferencia = await cliente_gemini.generar_json(
        tipo="inferir_estado", prompt=prompt, id_tarea=tarea.id_tarea, tokens_json_equivalente=json_equivalente
    )
    estado_act = await estado_service.estado_actual(db, tarea.id_tarea)

    if inferencia is None:
        inferencia = _inferir_determinista(texto)

    await conversacion_repo.registrar_respuesta(tarea.id_tarea, texto, inferencia)

    resumen = inferencia.get("resumen") or ""
    contexto_bloqueo = inferencia.get("contexto_bloqueo")
    try:
        estado_inferido = EstadoTarea(str(inferencia.get("estado", "EN_PROGRESO")).upper())
    except ValueError:
        estado_inferido = EstadoTarea.EN_PROGRESO

    genero_bloqueo = False
    if estado_inferido == EstadoTarea.BLOQUEADA:
        await bloqueo_service.registrar_bloqueo(
            db, tarea, contexto_bloqueo or resumen or "Bloqueo detectado en seguimiento"
        )
        genero_bloqueo = True
        siguiente = "Entiendo, anoté el impedimento y se lo paso al Scrum Master para destrabarte. ¿Querés contarme algo más mientras tanto?"
    elif estado_inferido == EstadoTarea.COMPLETADA:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.COMPLETADA)
        siguiente = "¡Genial, marqué la tarea como completada! 🎉 Gracias por el laburo."
    else:
        if estado_act in {EstadoTarea.ASIGNADA, EstadoTarea.BLOQUEADA}:
            await estado_service.cambiar_estado(db, tarea, EstadoTarea.EN_PROGRESO)
        siguiente = (await generar_consulta(db, tarea)).pregunta

    if siguiente and estado_inferido != EstadoTarea.EN_PROGRESO:
        await conversacion_repo.agregar_consulta(tarea.id_tarea, tarea.id_usuario_asignado, siguiente)

    return ResultadoSeguimiento(
        id_tarea=tarea.id_tarea, estado_inferido=estado_inferido, resumen=resumen,
        siguiente_pregunta=siguiente, genero_bloqueo=genero_bloqueo,
    )
