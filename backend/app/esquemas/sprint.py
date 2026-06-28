"""Esquemas de Sprint (CU9)."""
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.modelos.enums import EstadoSprint


class SprintCrear(BaseModel):
    objetivo: str
    fecha_inicio: date
    fecha_fin: date


class SprintActualizar(BaseModel):
    objetivo: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    estado: EstadoSprint | None = None


class SprintSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_sprint: int
    objetivo: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoSprint
