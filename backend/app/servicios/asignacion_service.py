"""Asignación automática de tareas (CU3, RF2/RF3/RF4/RF5/RF11)."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.esquemas.tarea import ResultadoAsignacion
from app.ia import cliente_gemini, prompts
from app.modelos.enums import EstadoTarea, RolNombre, valor
from app.modelos.tarea import Tarea
from app.repositorios import notificacion_repo, perfil_repo
from app.servicios import estado_service
from app.servicios.carga_service import calcular_carga
from app.servicios.notificacion_service import notificar_a_rol
from app.servicios.usuario_service import listar_por_rol

UMBRAL_CONFIANZA = 0.4


def _habilidades(tarea: Tarea) -> list[str]:
    return [h.strip() for h in (tarea.habilidades_requeridas or "").split(",") if h.strip()]


async def _notificar_lider(db: AsyncSession, mensaje: str, id_tarea: int) -> None:
    await notificar_a_rol(
        db, RolNombre.LIDER_TECNICO, "asignacion_requiere_atencion", mensaje, {"id_tarea": id_tarea}
    )


async def _historial_similares(db: AsyncSession, id_usuario: int, habilidades: list[str]) -> int:
    """Tareas completadas del dev que comparten alguna habilidad con la nueva."""
    filas = (
        await db.execute(
            select(Tarea.id_tarea, Tarea.habilidades_requeridas).where(
                Tarea.id_usuario_asignado == id_usuario
            )
        )
    ).all()
    if not filas:
        return 0
    estados = await estado_service.estados_actuales(db, [f[0] for f in filas])
    objetivo = {h.lower() for h in habilidades}
    return sum(
        1
        for id_tarea, hab in filas
        if estados.get(id_tarea) == EstadoTarea.COMPLETADA
        and objetivo & {h.strip().lower() for h in (hab or "").split(",") if h.strip()}
    )


async def _candidatos(db: AsyncSession, habilidades: list[str]) -> list[dict]:
    candidatos = []
    for dev in await listar_por_rol(db, RolNombre.DESARROLLADOR):
        perfil = await perfil_repo.obtener_perfil(dev.id_usuario) or {}
        candidatos.append(
            {
                "id": dev.id_usuario,
                "nombre": dev.nombre,
                "seniority": perfil.get("seniority") or "N/D",
                "lenguajes": perfil.get("lenguajes", []),
                "dominios": perfil.get("dominios", []),
                "frameworks": perfil.get("frameworks", []),
                "carga": await calcular_carga(db, dev.id_usuario),
                "tareas_similares_completadas": await _historial_similares(db, dev.id_usuario, habilidades),
            }
        )
    return candidatos


async def asignar_manual(db: AsyncSession, tarea: Tarea, id_usuario: int) -> ResultadoAsignacion:
    """El TL asigna a mano (ej. cuando la IA no tuvo confianza). El dev sumará las
    habilidades inferidas de la tarea al completarla (mismo flujo que la asignación IA)."""
    devs = {d.id_usuario for d in await listar_por_rol(db, RolNombre.DESARROLLADOR)}
    if id_usuario not in devs:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El usuario no es un desarrollador disponible")
    estado = await estado_service.estado_actual(db, tarea.id_tarea)
    if estado == EstadoTarea.COMPLETADA:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se puede reasignar una tarea completada")

    tarea.id_usuario_asignado = id_usuario
    if estado != EstadoTarea.ASIGNADA:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.ASIGNADA)
    await notificacion_repo.crear_notificacion(
        id_usuario, "tarea_asignada",
        f"Se te asignó manualmente la tarea #{tarea.id_tarea}: {tarea.descripcion}",
        {"id_tarea": tarea.id_tarea},
    )
    await db.flush()
    return ResultadoAsignacion(
        id_tarea=tarea.id_tarea, id_usuario_asignado=id_usuario, estado=EstadoTarea.ASIGNADA,
        motivo="Asignación manual del Líder Técnico", confianza=1.0,
    )


async def asignar_tarea(db: AsyncSession, tarea: Tarea) -> ResultadoAsignacion:
    habilidades = _habilidades(tarea)
    candidatos = await _candidatos(db, habilidades)

    if not candidatos:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.PENDIENTE_ASIGNACION)
        await _notificar_lider(db, f"Tarea #{tarea.id_tarea} sin desarrolladores para asignar.", tarea.id_tarea)
        return ResultadoAsignacion(
            id_tarea=tarea.id_tarea, id_usuario_asignado=None,
            estado=EstadoTarea.PENDIENTE_ASIGNACION, motivo="Sin desarrolladores disponibles",
        )

    tarea_payload = {
        "id": tarea.id_tarea,
        "descripcion": tarea.descripcion,
        "prioridad": valor(tarea.prioridad),
        "habilidades_requeridas": habilidades,
    }
    prompt, json_equivalente = prompts.prompt_asignacion(tarea_payload, candidatos)
    resultado = await cliente_gemini.generar_json(
        tipo="asignacion", prompt=prompt, id_tarea=tarea.id_tarea, tokens_json_equivalente=json_equivalente
    )

    if resultado is None:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.ASIGNACION_FALLIDA)
        await _notificar_lider(db, f"Asignación fallida de la tarea #{tarea.id_tarea} (IA no respondió).", tarea.id_tarea)
        return ResultadoAsignacion(
            id_tarea=tarea.id_tarea, id_usuario_asignado=None,
            estado=EstadoTarea.ASIGNACION_FALLIDA, motivo="La IA no respondió",
        )

    id_dev = resultado.get("id_usuario_asignado")
    confianza = float(resultado.get("confianza") or 0.0)
    motivo = resultado.get("motivo") or ""
    ids_validos = {c["id"] for c in candidatos}

    if id_dev not in ids_validos or confianza < UMBRAL_CONFIANZA:
        await _notificar_lider(
            db,
            f"La IA no encontró ajuste suficiente para la tarea #{tarea.id_tarea}. Requiere asignación manual.",
            tarea.id_tarea,
        )
        estado = await estado_service.estado_actual(db, tarea.id_tarea)
        return ResultadoAsignacion(
            id_tarea=tarea.id_tarea, id_usuario_asignado=None, estado=estado,
            motivo="Ningún desarrollador es acorde para la tarea", confianza=confianza,
        )

    # Guardamos las habilidades que infirió la IA: alimentan el histórico al completar.
    if not habilidades:
        inferidas = [str(h).strip() for h in (resultado.get("habilidades_inferidas") or []) if str(h).strip()]
        if inferidas:
            tarea.habilidades_requeridas = ", ".join(inferidas)

    tarea.id_usuario_asignado = id_dev
    await estado_service.cambiar_estado(db, tarea, EstadoTarea.ASIGNADA)
    await notificacion_repo.crear_notificacion(
        id_dev, "tarea_asignada",
        f"Se te asignó la tarea #{tarea.id_tarea}: {tarea.descripcion}",
        {"id_tarea": tarea.id_tarea, "motivo": motivo},
    )
    return ResultadoAsignacion(
        id_tarea=tarea.id_tarea, id_usuario_asignado=id_dev, estado=EstadoTarea.ASIGNADA,
        motivo=motivo, confianza=confianza,
    )
