"""Notificación dirigida a todos los usuarios de un rol (RF5/RF9/RF13)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.modelos.enums import RolNombre
from app.repositorios import notificacion_repo
from app.servicios.usuario_service import listar_por_rol


async def notificar_a_rol(
    db: AsyncSession, rol: RolNombre, tipo: str, mensaje: str, data: dict | None = None
) -> None:
    for usuario in await listar_por_rol(db, rol):
        await notificacion_repo.crear_notificacion(usuario.id_usuario, tipo, mensaje, data)
