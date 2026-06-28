"""Gestión de bloqueos (CU5, RF9/RF13)."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.esquemas.bloqueo import ResolverBloqueoEntrada
from app.modelos.bloqueo import Bloqueo
from app.modelos.enums import EstadoBloqueo, EstadoTarea, RolNombre
from app.modelos.tarea import Tarea
from app.repositorios import conversacion_repo, notificacion_repo
from app.servicios import estado_service
from app.servicios.notificacion_service import notificar_a_rol


async def registrar_bloqueo(db: AsyncSession, tarea: Tarea, contexto: str) -> Bloqueo:
    """Crea el bloqueo, pasa la tarea a BLOQUEADA y escala al SM (RF9)."""
    bloqueo = Bloqueo(id_tarea=tarea.id_tarea, contexto=contexto, estado=EstadoBloqueo.ABIERTO)
    db.add(bloqueo)
    if await estado_service.estado_actual(db, tarea.id_tarea) != EstadoTarea.BLOQUEADA:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.BLOQUEADA)
    await db.flush()

    await notificar_a_rol(
        db, RolNombre.SCRUM_MASTER, "bloqueo_detectado",
        f"Bloqueo en la tarea #{tarea.id_tarea}: {contexto}",
        {"id_tarea": tarea.id_tarea, "id_bloqueo": bloqueo.id_bloqueo},
    )
    return bloqueo

_ESTADOS_PENDIENTES = [EstadoBloqueo.ABIERTO, EstadoBloqueo.PERSISTENTE, EstadoBloqueo.ESCALADO_TL]
# El SM no ve los elevados: pasan a ser responsabilidad del TL (aparecen en Informes).
_ESTADOS_SM = [EstadoBloqueo.ABIERTO, EstadoBloqueo.PERSISTENTE]


async def listar_abiertos(db: AsyncSession) -> list[Bloqueo]:
    return list(
        (
            await db.execute(select(Bloqueo).where(Bloqueo.estado.in_(_ESTADOS_SM)))
        ).scalars().all()
    )


async def listar_por_estado(db: AsyncSession, estado: EstadoBloqueo) -> list[Bloqueo]:
    return list((await db.execute(select(Bloqueo).where(Bloqueo.estado == estado))).scalars().all())


async def obtener(db: AsyncSession, id_bloqueo: int) -> Bloqueo | None:
    return await db.get(Bloqueo, id_bloqueo)


async def cerrar_pendientes_de_tarea(
    db: AsyncSession, id_tarea: int, motivo: str = "Cerrado automáticamente al completarse la tarea"
) -> None:
    filas = (
        await db.execute(
            select(Bloqueo).where(Bloqueo.id_tarea == id_tarea, Bloqueo.estado.in_(_ESTADOS_PENDIENTES))
        )
    ).scalars().all()
    for bloqueo in filas:
        bloqueo.estado = EstadoBloqueo.RESUELTO
        bloqueo.resolucion = bloqueo.resolucion or motivo
        bloqueo.fecha_resolucion = datetime.now(timezone.utc)
    if filas:
        await db.flush()

async def resolver_bloqueo(
    db: AsyncSession, id_bloqueo: int, id_sm: int, data: ResolverBloqueoEntrada
) -> Bloqueo:
    bloqueo = await db.get(Bloqueo, id_bloqueo)
    if bloqueo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloqueo inexistente")

    bloqueo.resolucion = data.resolucion
    bloqueo.id_usuario_sm = id_sm
    tarea = await db.get(Tarea, bloqueo.id_tarea)

    if data.escalar_a_tl:
        bloqueo.estado = EstadoBloqueo.ESCALADO_TL
        if tarea is not None and (
            await estado_service.estado_actual(db, tarea.id_tarea) != EstadoTarea.COMPLETADA
        ):
            await estado_service.cambiar_estado(db, tarea, EstadoTarea.EN_PROGRESO)
        await notificar_a_rol(
            db, RolNombre.LIDER_TECNICO, "bloqueo_escalado",
            f"El SM elevó la tarea #{bloqueo.id_tarea} para tu revisión.",
            {"id_tarea": bloqueo.id_tarea, "id_bloqueo": bloqueo.id_bloqueo},
        )
        await db.flush()
        return bloqueo

    if data.persistente:
        bloqueo.estado = EstadoBloqueo.PERSISTENTE
        await db.flush()
        return bloqueo

    bloqueo.estado = EstadoBloqueo.RESUELTO
    bloqueo.fecha_resolucion = datetime.now(timezone.utc)
    tarea_completada = tarea is not None and (
        await estado_service.estado_actual(db, tarea.id_tarea) == EstadoTarea.COMPLETADA
    )
    if tarea is not None and not tarea_completada:
        await estado_service.cambiar_estado(db, tarea, EstadoTarea.EN_PROGRESO)
        if tarea.id_usuario_asignado is not None:
            await notificacion_repo.crear_notificacion(
                tarea.id_usuario_asignado, "tarea_desbloqueada",
                f"La tarea #{tarea.id_tarea} fue desbloqueada.", {"id_tarea": tarea.id_tarea},
            )
            await conversacion_repo.agregar_consulta(
                tarea.id_tarea, tarea.id_usuario_asignado,
                f"✅ El Scrum Master resolvió tu bloqueo: «{data.resolucion}». "
                f"Ya podés continuar con la tarea. ¿Cómo seguís?",
            )
    await db.flush()
    return bloqueo
