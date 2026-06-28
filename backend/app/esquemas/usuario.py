"""Esquemas de Usuario / Desarrollador (CU2)."""
from pydantic import BaseModel, EmailStr, Field

from app.modelos.enums import RolNombre


class PerfilEntrada(BaseModel):
    lenguajes: list[str] = Field(default_factory=list)
    dominios: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    seniority: str | None = None


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str
    rol: RolNombre = RolNombre.DESARROLLADOR
    perfil: PerfilEntrada = Field(default_factory=PerfilEntrada)


class UsuarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    password: str | None = None
    activo: bool | None = None
    perfil: PerfilEntrada | None = None


class UsuarioSalida(BaseModel):
    id_usuario: int
    nombre: str
    email: EmailStr
    rol: RolNombre
    activo: bool


class PerfilSalida(BaseModel):
    id_usuario_postgres: int
    lenguajes: list[str] = Field(default_factory=list)
    dominios: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    seniority: str | None = None
    historial_tareas: dict = Field(default_factory=dict)
    metricas_agregadas: dict = Field(default_factory=dict)
