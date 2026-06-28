"""Router del dashboard del sprint (CU7, RF14) y notificaciones (RF5/RF9/RF13)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import obtener_usuario_actual
from app.esquemas.auth import UsuarioActual
from app.modelos.enums import RolNombre
from app.repositorios import notificacion_repo
from app.servicios import dashboard_service

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard")
async def dashboard(
    db: AsyncSession = Depends(obtener_db),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
):
    """Vista personalizada según el rol del usuario autenticado."""
    if usuario.rol == RolNombre.DESARROLLADOR.value:
        return await dashboard_service.dashboard_desarrollador(db, usuario.id)
    return await dashboard_service.dashboard_global(db)


@router.get("/notificaciones")
async def mis_notificaciones(
    solo_no_leidas: bool = False,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
):
    return await notificacion_repo.listar_por_usuario(usuario.id, solo_no_leidas)
