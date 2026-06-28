"""Cálculo de la carga de trabajo por desarrollador (CU3 paso 3, RF3)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modelos.enums import EstadoTarea
from app.modelos.tarea import Tarea
from app.servicios import estado_service

_PESOS: dict[EstadoTarea, float] = {
    EstadoTarea.ASIGNADA: 1.0,
    EstadoTarea.EN_PROGRESO: 1.5,
    EstadoTarea.BLOQUEADA: 0.5,
}


async def calcular_carga(db: AsyncSession, id_usuario: int) -> float:
    ids = (
        await db.execute(select(Tarea.id_tarea).where(Tarea.id_usuario_asignado == id_usuario))
    ).scalars().all()
    estados = await estado_service.estados_actuales(db, list(ids))
    return round(sum(_PESOS.get(estado, 0.0) for estado in estados.values()), 2)
