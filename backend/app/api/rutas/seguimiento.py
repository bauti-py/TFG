"""Router del seguimiento conversacional (CU4)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import obtener_usuario_actual
from app.esquemas.auth import UsuarioActual
from app.esquemas.seguimiento import (
    ConsultaAvanceSalida,
    EventoCronologia,
    MensajeConversacion,
    RespuestaAvanceEntrada,
    ResultadoSeguimiento,
    ResumenSeguimiento,
)
from app.modelos.enums import RolNombre
from app.repositorios import conversacion_repo
from app.servicios import seguimiento_service, tarea_service

router = APIRouter(prefix="/tareas/{id_tarea}/seguimiento", tags=["Seguimiento conversacional"])


@router.post("/consulta", response_model=ConsultaAvanceSalida)
async def generar_consulta(
    id_tarea: int, db: AsyncSession = Depends(obtener_db),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
):
    """Dispara la generación de la consulta de avance (RF6/RF12).

    La pueden disparar el SM/TL (seguimiento del equipo) o el propio desarrollador
    asignado al abrir su chat de avance.
    """
    tarea = await tarea_service.obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    es_dev_asignado = (
        usuario.rol == RolNombre.DESARROLLADOR.value and tarea.id_usuario_asignado == usuario.id
    )
    es_gestor = usuario.rol in {RolNombre.SCRUM_MASTER.value, RolNombre.LIDER_TECNICO.value}
    if not (es_dev_asignado or es_gestor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No podés generar la consulta de esta tarea")
    return await seguimiento_service.generar_consulta(db, tarea)


@router.post("/respuesta", response_model=ResultadoSeguimiento)
async def responder(
    id_tarea: int, data: RespuestaAvanceEntrada, db: AsyncSession = Depends(obtener_db),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
):
    """El desarrollador responde la consulta; la IA infiere el estado (RF7)."""
    tarea = await tarea_service.obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    if usuario.rol == RolNombre.DESARROLLADOR.value and tarea.id_usuario_asignado != usuario.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La tarea no está asignada a este usuario")
    return await seguimiento_service.procesar_respuesta(db, tarea, data.texto)


@router.post("/resumen", response_model=ResumenSeguimiento)
async def resumir(
    id_tarea: int, db: AsyncSession = Depends(obtener_db),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
):
    """Resumen IA de la conversación de avance, para SM y TL."""
    if usuario.rol not in {RolNombre.SCRUM_MASTER.value, RolNombre.LIDER_TECNICO.value}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el SM o el TL pueden pedir el resumen")
    tarea = await tarea_service.obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    return ResumenSeguimiento(id_tarea=id_tarea, resumen=await seguimiento_service.resumir_conversacion(db, tarea))


@router.get("/cronologia", response_model=list[EventoCronologia])
async def ver_cronologia(
    id_tarea: int, db: AsyncSession = Depends(obtener_db),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
):
    """Línea de tiempo de la tarea (comentarios + cambios de estado) para SM y TL."""
    if usuario.rol not in {RolNombre.SCRUM_MASTER.value, RolNombre.LIDER_TECNICO.value}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el SM o el TL pueden ver la cronología")
    tarea = await tarea_service.obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    return await seguimiento_service.cronologia(db, tarea)


@router.get("/conversacion", response_model=list[MensajeConversacion],
            dependencies=[Depends(obtener_usuario_actual)])
async def ver_conversacion(id_tarea: int):
    mensajes: list[MensajeConversacion] = []
    for ciclo in await conversacion_repo.listar_por_tarea(id_tarea):
        if ciclo.get("consulta") and ciclo.get("fecha_consulta"):
            mensajes.append(
                MensajeConversacion(autor="sistema", texto=ciclo["consulta"]["texto"], fecha=ciclo["fecha_consulta"])
            )
        if ciclo.get("respuesta") and ciclo.get("fecha_respuesta"):
            mensajes.append(
                MensajeConversacion(autor="desarrollador", texto=ciclo["respuesta"]["texto"], fecha=ciclo["fecha_respuesta"])
            )
    return mensajes
