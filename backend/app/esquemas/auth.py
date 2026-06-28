"""Esquemas de autenticación (CU10)."""
from pydantic import BaseModel, EmailStr


class SolicitudLogin(BaseModel):
    email: EmailStr
    password: str


class RespuestaToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    id_usuario: int
    nombre: str


class UsuarioActual(BaseModel):
    """Identidad extraída del JWT para inyectar en endpoints protegidos."""
    id: int
    rol: str
