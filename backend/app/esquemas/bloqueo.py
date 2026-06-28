"""Esquemas de Bloqueo (CU5)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modelos.enums import EstadoBloqueo


class BloqueoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_bloqueo: int
    id_tarea: int
    descripcion_tarea: str | None = None
    id_usuario_asignado: int | None = None
    contexto: str
    estado: EstadoBloqueo
    resolucion: str | None
    fecha_deteccion: datetime
    fecha_resolucion: datetime | None


class ResolverBloqueoEntrada(BaseModel):
    resolucion: str
    persistente: bool = False
    escalar_a_tl: bool = False


class TareaElevada(BaseModel):
    id_tarea: int
    descripcion: str | None
    contexto: str
