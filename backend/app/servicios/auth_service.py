"""Servicio de autenticación (CU10, RF21/RF22)."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.seguridad import crear_token, verificar_password
from app.esquemas.auth import RespuestaToken
from app.modelos.enums import valor
from app.repositorios import auditoria_repo
from app.servicios.usuario_service import obtener_por_email

_EVENTO_FALLIDO = "login_fallido"


async def login(db: AsyncSession, email: str, password: str) -> RespuestaToken:
    usuario = await obtener_por_email(db, email)
    if usuario is None or not usuario.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")

    desde = datetime.now(timezone.utc) - timedelta(minutes=config.BLOQUEO_MINUTOS)
    fallidos = await auditoria_repo.contar_eventos_recientes(_EVENTO_FALLIDO, usuario.id_usuario, desde)
    if fallidos >= config.MAX_INTENTOS_LOGIN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Cuenta bloqueada temporalmente por {config.BLOQUEO_MINUTOS} minutos tras varios intentos fallidos",
        )

    if not verificar_password(password, usuario.contrasena_hash):
        await auditoria_repo.registrar_evento(
            tipo_evento=_EVENTO_FALLIDO, contexto={"email": email}, id_usuario_postgres=usuario.id_usuario
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")

    rol = valor(usuario.rol.nombre)
    token = crear_token(id_usuario=usuario.id_usuario, rol=rol)
    return RespuestaToken(
        access_token=token, rol=rol, id_usuario=usuario.id_usuario, nombre=usuario.nombre
    )
