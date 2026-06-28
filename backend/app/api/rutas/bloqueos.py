"""Router de gestión de bloqueos (CU5). Atribución del Scrum Master."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import requiere_rol
from app.esquemas.auth import UsuarioActual
from app.esquemas.bloqueo import BloqueoSalida, ResolverBloqueoEntrada
from app.modelos.enums import EstadoBloqueo, RolNombre
from app.servicios import bloqueo_service, tarea_service


def _a_salida(b, descripciones: dict[int, str], asignados: dict[int, int | None]) -> BloqueoSalida:
    return BloqueoSalida(
        id_bloqueo=b.id_bloqueo, id_tarea=b.id_tarea, descripcion_tarea=descripciones.get(b.id_tarea),
        id_usuario_asignado=asignados.get(b.id_tarea),
        contexto=b.contexto, estado=b.estado, resolucion=b.resolucion,
        fecha_deteccion=b.fecha_deteccion, fecha_resolucion=b.fecha_resolucion,
    )

router = APIRouter(prefix="/bloqueos", tags=["Bloqueos"])

_solo_sm = requiere_rol(RolNombre.SCRUM_MASTER)
_solo_tl = requiere_rol(RolNombre.LIDER_TECNICO)


@router.get("", response_model=list[BloqueoSalida], dependencies=[Depends(_solo_sm)])
async def listar(db: AsyncSession = Depends(obtener_db)):
    bloqueos = await bloqueo_service.listar_abiertos(db)
    ids = [b.id_tarea for b in bloqueos]
    descripciones = await tarea_service.descripciones(db, ids)
    asignados = await tarea_service.asignados(db, ids)
    return [_a_salida(b, descripciones, asignados) for b in bloqueos]


@router.get("/elevados", response_model=list[BloqueoSalida], dependencies=[Depends(_solo_tl)])
async def elevados(db: AsyncSession = Depends(obtener_db)):
    bloqueos = await bloqueo_service.listar_por_estado(db, EstadoBloqueo.ESCALADO_TL)
    ids = [b.id_tarea for b in bloqueos]
    descripciones = await tarea_service.descripciones(db, ids)
    asignados = await tarea_service.asignados(db, ids)
    return [_a_salida(b, descripciones, asignados) for b in bloqueos]


@router.post("/{id_bloqueo}/resolver", response_model=BloqueoSalida)
async def resolver(
    id_bloqueo: int, data: ResolverBloqueoEntrada, db: AsyncSession = Depends(obtener_db),
    sm: UsuarioActual = Depends(_solo_sm),
):
    return await bloqueo_service.resolver_bloqueo(db, id_bloqueo, sm.id, data)


@router.post("/{id_bloqueo}/resolver-tl", response_model=BloqueoSalida)
async def resolver_tl(
    id_bloqueo: int, data: ResolverBloqueoEntrada, db: AsyncSession = Depends(obtener_db),
    tl: UsuarioActual = Depends(_solo_tl),
):
    """El TL cierra un bloqueo que el SM le elevó (mismo desbloqueo y aviso al dev)."""
    bloqueo = await bloqueo_service.obtener(db, id_bloqueo)
    if bloqueo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloqueo inexistente")
    if bloqueo.estado != EstadoBloqueo.ESCALADO_TL:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este bloqueo no fue elevado al Líder Técnico")
    return await bloqueo_service.resolver_bloqueo(db, id_bloqueo, tl.id, data)
