"""Router de backlog/tareas (CU1, CU3, CU6)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import obtener_usuario_actual, requiere_rol
from app.esquemas.tarea import (
    AsignacionManual,
    CambioEstadoEntrada,
    ResultadoAsignacion,
    TareaCrear,
    TareaSalida,
)
from app.modelos.enums import RolNombre
from app.servicios import estado_service, tarea_service

router = APIRouter(prefix="/sprints/{id_sprint}/tareas", tags=["Backlog / Tareas"])

_solo_tl = requiere_rol(RolNombre.LIDER_TECNICO)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(_solo_tl)])
async def registrar(id_sprint: int, data: TareaCrear, db: AsyncSession = Depends(obtener_db)):
    """Registra una tarea en el backlog y dispara la asignación automática (RF1)."""
    tarea, resultado = await tarea_service.registrar_tarea(db, id_sprint, data)
    return {"tarea": await tarea_service.a_salida(db, tarea), "asignacion": resultado}


@router.get("", response_model=list[TareaSalida], dependencies=[Depends(obtener_usuario_actual)])
async def listar(id_sprint: int, db: AsyncSession = Depends(obtener_db)):
    tareas = await tarea_service.listar_por_sprint(db, id_sprint)
    return [await tarea_service.a_salida(db, t) for t in tareas]


tareas_router = APIRouter(prefix="/tareas", tags=["Backlog / Tareas"])


@tareas_router.post("/{id_tarea}/reasignar", response_model=ResultadoAsignacion,
                    dependencies=[Depends(_solo_tl)])
async def reasignar(id_tarea: int, db: AsyncSession = Depends(obtener_db)):
    return await tarea_service.reasignar(db, id_tarea)


@tareas_router.post("/{id_tarea}/asignar", response_model=ResultadoAsignacion,
                    dependencies=[Depends(_solo_tl)])
async def asignar_manual(id_tarea: int, data: AsignacionManual, db: AsyncSession = Depends(obtener_db)):
    """El Líder Técnico asigna la tarea a un desarrollador a mano."""
    return await tarea_service.asignar_manual(db, id_tarea, data.id_usuario)


@tareas_router.delete("/{id_tarea}", status_code=status.HTTP_204_NO_CONTENT,
                      dependencies=[Depends(_solo_tl)])
async def eliminar(id_tarea: int, db: AsyncSession = Depends(obtener_db)):
    await tarea_service.eliminar(db, id_tarea)


@tareas_router.patch("/{id_tarea}/estado", response_model=TareaSalida)
async def cambiar_estado(
    id_tarea: int, data: CambioEstadoEntrada, db: AsyncSession = Depends(obtener_db),
    usuario=Depends(obtener_usuario_actual),
):
    """Cambio manual de estado con validación de la máquina de transiciones (CU6)."""
    tarea = await tarea_service.obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    await estado_service.cambiar_estado(db, tarea, data.nuevo_estado)
    return await tarea_service.a_salida(db, tarea)
