"""Dependencias transversales de la API: autenticación JWT y control de acceso"""
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.seguridad import decodificar_token
from app.esquemas.auth import UsuarioActual
from app.modelos.enums import RolNombre

_bearer = HTTPBearer(auto_error=False)


async def obtener_usuario_actual(
    credencial: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UsuarioActual:
    if credencial is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token de autenticación")
    payload = decodificar_token(credencial.credentials)
    if payload is None or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")
    return UsuarioActual(id=int(payload["sub"]), rol=payload.get("rol", ""))


def requiere_rol(*roles: RolNombre) -> Callable:
    """Fábrica de dependencia que restringe un endpoint a ciertos roles."""
    permitidos = {r.value for r in roles}

    async def _verificar(
        usuario: UsuarioActual = Depends(obtener_usuario_actual),
    ) -> UsuarioActual:
        if usuario.rol not in permitidos:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Acceso denegado: requiere rol {', '.join(permitidos)}",
            )
        return usuario

    return _verificar
