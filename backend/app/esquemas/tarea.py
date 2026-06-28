"""Esquemas de Tarea (CU1, CU3, CU6)."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.modelos.enums import EstadoTarea, Prioridad


class TareaCrear(BaseModel):
    descripcion: str = Field(min_length=3)
    prioridad: Prioridad = Prioridad.MEDIA
    habilidades_requeridas: list[str] = Field(default_factory=list)


class TareaSalida(BaseModel):
    id_tarea: int
    descripcion: str
    prioridad: Prioridad
    habilidades_requeridas: list[str]
    estado: EstadoTarea
    id_sprint: int
    id_usuario_asignado: int | None
    fecha_creacion: datetime
    fecha_cierre: datetime | None


class CambioEstadoEntrada(BaseModel):
    nuevo_estado: EstadoTarea


class AsignacionManual(BaseModel):
    id_usuario: int


class ResultadoAsignacion(BaseModel):
    id_tarea: int
    id_usuario_asignado: int | None
    estado: EstadoTarea
    motivo: str | None = None
    confianza: float | None = None
