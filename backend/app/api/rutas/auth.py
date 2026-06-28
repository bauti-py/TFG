"""Router de autenticación (CU10)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import obtener_usuario_actual
from app.esquemas.auth import RespuestaToken, SolicitudLogin, UsuarioActual
from app.servicios import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=RespuestaToken)
async def login(data: SolicitudLogin, db: AsyncSession = Depends(obtener_db)):
    return await auth_service.login(db, data.email, data.password)


@router.post("/logout")
async def logout(usuario: UsuarioActual = Depends(obtener_usuario_actual)):
    return {"mensaje": "Sesión finalizada"}


@router.get("/yo", response_model=UsuarioActual)
async def yo(usuario: UsuarioActual = Depends(obtener_usuario_actual)):
    return usuario
