"""Seguimiento conversacional asincrónico (CU4, RF6/RF7/RF12)."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.esquemas.seguimiento import ConsultaAvanceSalida, ResultadoSeguimiento
from app.ia import cliente_gemini, prompts
from app.modelos.enums import EstadoTarea
from app.modelos.tarea import Tarea
from app.modelos.transicion_estado import TransicionEstado
from app.repositorios import conversacion_repo, perfil_repo
from app.servicios import bloqueo_service, estado_service
from app.servicios.usuario_service import obtener_por_id


# Estados que se muestran en la cronología como hito (el resto es ruido de asignación).
_ESTADOS_HITO = {
    EstadoTarea.ASIGNADA, EstadoTarea.EN_PROGRESO, EstadoTarea.BLOQUEADA, EstadoTarea.COMPLETADA,
}


async def cronologia(db: AsyncSession, tarea: Tarea) -> list[dict]:
    """Historial de estados (hitos) de la tarea, por fecha. El detalle conversacional lo da la IA."""
    transiciones = (
        await db.execute(
            select(TransicionEstado.estado, TransicionEstado.fecha_transicion)
            .where(TransicionEstado.id_tarea == tarea.id_tarea)
            .order_by(TransicionEstado.fecha_transicion.asc())
        )
    ).all()
    eventos: list[dict] = []
    for estado, fecha in transiciones:
        try:
            est = EstadoTarea(estado)
        except ValueError:
            continue
        if est in _ESTADOS_HITO:
            eventos.append({"tipo": "estado", "fecha": fecha, "estado": est.value})
    return eventos


# El estado lo decide siempre la IA (ver prompt_inferir_estado). No hay heurísticas de
# palabras clave: si Gemini no está disponible, la respuesta queda diferida (ver más abajo).


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

    # Sin IA disponible (sin key / cuota agotada / timeout): NO adivinamos el estado con
    # heurísticas. Guardamos la respuesta como diferida, no tocamos el estado de la tarea
    # (evita falsos bloqueos) y avisamos al desarrollador. Se retoma cuando la IA vuelva.
    if inferencia is None:
        await conversacion_repo.registrar_respuesta(tarea.id_tarea, texto, None, diferido=True)
        aviso = "Recibí tu mensaje y lo registré. El asistente está sin servicio por ahora; lo retomo apenas vuelva. 🙏"
        return ResultadoSeguimiento(
            id_tarea=tarea.id_tarea, estado_inferido=estado_act, resumen=aviso,
            siguiente_pregunta=aviso, genero_bloqueo=False, diferido=True,
        )

    await conversacion_repo.registrar_respuesta(tarea.id_tarea, texto, inferencia)

    resumen = inferencia.get("resumen") or ""
    contexto_bloqueo = inferencia.get("contexto_bloqueo")
    try:
        estado_inferido = EstadoTarea(str(inferencia.get("estado", "EN_PROGRESO")).upper())
    except ValueError:
        estado_inferido = EstadoTarea.EN_PROGRESO

    # La IA decide si tiene sentido seguir preguntando o cerrar la charla (no insistir).
    continuar = bool(inferencia.get("continuar", True))
    cierre = (inferencia.get("cierre") or "").strip()

    genero_bloqueo = False
    if estado_inferido == EstadoTarea.BLOQUEADA:
        await bloqueo_service.registrar_bloqueo(
            db, tarea, contexto_bloqueo or resumen or "Bloqueo detectado en seguimiento"
        )
        genero_bloqueo = True
        siguiente = "Entiendo, anoté el impedimento y se lo paso al Scrum Master para destrabarte. 🙌"
    elif estado_inferido == EstadoTarea.COMPLETADA:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.COMPLETADA)
        siguiente = "¡Genial, marqué la tarea como completada! 🎉 Gracias por el laburo."
    else:
        if estado_act in {EstadoTarea.ASIGNADA, EstadoTarea.BLOQUEADA}:
            await estado_service.cambiar_estado(db, tarea, EstadoTarea.EN_PROGRESO)
        if continuar:
            # Solo acá se persiste una consulta nueva → la conversación queda "pendiente".
            siguiente = (await generar_consulta(db, tarea)).pregunta
        else:
            siguiente = cierre or "¡Perfecto! Lo dejo acá. Cuando tengas novedades me escribís 👍"

    # Los cierres y acks NO se persisten como consulta: así la charla no queda marcada como
    # pendiente y la IA no vuelve a preguntar sola. Solo se muestran como respuesta del momento.

    return ResultadoSeguimiento(
        id_tarea=tarea.id_tarea, estado_inferido=estado_inferido, resumen=resumen,
        siguiente_pregunta=siguiente, genero_bloqueo=genero_bloqueo,
    )
