"""Máquina de transiciones y estado de tareas (CU6, RF8/RF10)."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modelos.enums import EstadoTarea, RolNombre
from app.modelos.tarea import Tarea
from app.modelos.transicion_estado import TransicionEstado
from app.repositorios import auditoria_repo
from app.servicios import bloqueo_service, perfil_service
from app.servicios.notificacion_service import notificar_a_rol

TRANSICIONES: dict[EstadoTarea, set[EstadoTarea]] = {
    EstadoTarea.PENDIENTE: {EstadoTarea.ASIGNADA, EstadoTarea.PENDIENTE_ASIGNACION, EstadoTarea.ASIGNACION_FALLIDA},
    EstadoTarea.PENDIENTE_ASIGNACION: {EstadoTarea.ASIGNADA, EstadoTarea.ASIGNACION_FALLIDA},
    EstadoTarea.ASIGNACION_FALLIDA: {EstadoTarea.ASIGNADA},
    EstadoTarea.ASIGNADA: {EstadoTarea.EN_PROGRESO, EstadoTarea.BLOQUEADA, EstadoTarea.COMPLETADA},
    EstadoTarea.EN_PROGRESO: {EstadoTarea.BLOQUEADA, EstadoTarea.COMPLETADA},
    EstadoTarea.BLOQUEADA: {EstadoTarea.EN_PROGRESO, EstadoTarea.COMPLETADA},
    EstadoTarea.COMPLETADA: set(),
}


def transicion_valida(actual: EstadoTarea, nuevo: EstadoTarea) -> bool:
    if actual == nuevo:
        return True
    return nuevo in TRANSICIONES.get(actual, set())


async def estado_actual(db: AsyncSession, id_tarea: int) -> EstadoTarea:
    fila = (
        await db.execute(
            select(TransicionEstado.estado)
            .where(TransicionEstado.id_tarea == id_tarea)
            .order_by(TransicionEstado.id_transicion.desc())
            .limit(1)
        )
    ).scalars().first()
    return EstadoTarea(fila) if fila is not None else EstadoTarea.PENDIENTE


async def estados_actuales(db: AsyncSession, ids_tarea: list[int]) -> dict[int, EstadoTarea]:
    """Estado actual de varias tareas en una sola consulta (última transición por tarea)."""
    if not ids_tarea:
        return {}
    sub = (
        select(func.max(TransicionEstado.id_transicion).label("ultima"))
        .where(TransicionEstado.id_tarea.in_(ids_tarea))
        .group_by(TransicionEstado.id_tarea)
        .subquery()
    )
    filas = (
        await db.execute(
            select(TransicionEstado.id_tarea, TransicionEstado.estado).join(
                sub, TransicionEstado.id_transicion == sub.c.ultima
            )
        )
    ).all()
    mapa = {id_tarea: EstadoTarea(estado) for id_tarea, estado in filas}
    return {id_tarea: mapa.get(id_tarea, EstadoTarea.PENDIENTE) for id_tarea in ids_tarea}


async def registrar_estado_inicial(db: AsyncSession, tarea: Tarea) -> None:
    db.add(TransicionEstado(id_tarea=tarea.id_tarea, estado=EstadoTarea.PENDIENTE))
    await db.flush()


async def cambiar_estado(
    db: AsyncSession, tarea: Tarea, nuevo_estado: EstadoTarea, validar: bool = True
) -> EstadoTarea:
    actual = await estado_actual(db, tarea.id_tarea)

    if validar and not transicion_valida(actual, nuevo_estado):
        await auditoria_repo.registrar_evento(
            tipo_evento="transicion_rechazada",
            contexto={"desde": actual.value, "hacia": nuevo_estado.value},
            id_tarea_postgres=tarea.id_tarea,
        )
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"No se puede pasar de {actual.value} a {nuevo_estado.value}"
        )

    db.add(TransicionEstado(id_tarea=tarea.id_tarea, estado=nuevo_estado))
    if nuevo_estado == EstadoTarea.COMPLETADA:
        tarea.fecha_cierre = datetime.now(timezone.utc)
        await _al_completar(db, tarea)
    await db.flush()
    return nuevo_estado


def _habilidades(tarea: Tarea) -> list[str]:
    return [h.strip() for h in (tarea.habilidades_requeridas or "").split(",") if h.strip()]


async def _al_completar(db: AsyncSession, tarea: Tarea) -> None:
    await bloqueo_service.cerrar_pendientes_de_tarea(db, tarea.id_tarea)
    await notificar_a_rol(
        db, RolNombre.SCRUM_MASTER, "tarea_completada",
        f"La tarea #{tarea.id_tarea} fue completada.", {"id_tarea": tarea.id_tarea},
    )
    if tarea.id_usuario_asignado is not None:
        await perfil_service.actualizar_por_tarea_completada(tarea.id_usuario_asignado, _habilidades(tarea))
