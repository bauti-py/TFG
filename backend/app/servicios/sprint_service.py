"""Servicio de sprints (CU9, RF15-17)."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.esquemas.sprint import SprintActualizar, SprintCrear
from app.modelos.enums import EstadoSprint
from app.modelos.sprint import Sprint


async def crear_sprint(db: AsyncSession, data: SprintCrear) -> Sprint:
    if data.fecha_fin < data.fecha_inicio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La fecha de fin no puede ser anterior a la de inicio")
    sprint = Sprint(
        objetivo=data.objetivo,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        estado=EstadoSprint.PLANIFICADO,
    )
    db.add(sprint)
    await db.flush()
    return sprint


async def listar_sprints(db: AsyncSession) -> list[Sprint]:
    return list(
        (await db.execute(select(Sprint).order_by(Sprint.fecha_inicio.desc()))).scalars().all()
    )


async def obtener_sprint_activo(db: AsyncSession) -> Sprint | None:
    return (
        await db.execute(select(Sprint).where(Sprint.estado == EstadoSprint.ACTIVO))
    ).scalars().first()


async def _obtener_o_404(db: AsyncSession, id_sprint: int) -> Sprint:
    sprint = await db.get(Sprint, id_sprint)
    if sprint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprint inexistente")
    return sprint


async def actualizar_sprint(db: AsyncSession, id_sprint: int, data: SprintActualizar) -> Sprint:
    sprint = await _obtener_o_404(db, id_sprint)
    nueva_inicio = data.fecha_inicio or sprint.fecha_inicio
    nueva_fin = data.fecha_fin or sprint.fecha_fin
    if nueva_fin < nueva_inicio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La fecha de fin no puede ser anterior a la de inicio")

    if data.objetivo is not None:
        sprint.objetivo = data.objetivo
    sprint.fecha_inicio = nueva_inicio
    sprint.fecha_fin = nueva_fin
    if data.estado is not None:
        sprint.estado = data.estado
    await db.flush()
    return sprint


async def eliminar_sprint(db: AsyncSession, id_sprint: int) -> None:
    """Elimina el sprint y su backlog asociado (RF17, cascade)."""
    sprint = await _obtener_o_404(db, id_sprint)
    await db.delete(sprint)
    await db.flush()
