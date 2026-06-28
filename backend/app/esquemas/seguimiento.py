"""Esquemas del seguimiento conversacional (CU4)."""
from datetime import datetime

from pydantic import BaseModel

from app.modelos.enums import EstadoTarea


class ConsultaAvanceSalida(BaseModel):
    id_tarea: int
    pregunta: str


class RespuestaAvanceEntrada(BaseModel):
    texto: str


class ResultadoSeguimiento(BaseModel):
    id_tarea: int
    estado_inferido: EstadoTarea
    resumen: str
    siguiente_pregunta: str = ""
    genero_bloqueo: bool = False
    diferido: bool = False


class MensajeConversacion(BaseModel):
    autor: str
    texto: str
    fecha: datetime


class ResumenSeguimiento(BaseModel):
    id_tarea: int
    resumen: str


class EventoCronologia(BaseModel):
    tipo: str  # "comentario" | "estado"
    fecha: datetime
    autor: str | None = None
    texto: str | None = None
    estado: EstadoTarea | None = None


class TareaActividad(BaseModel):
    id_tarea: int
    descripcion: str
    estado: EstadoTarea
    fecha_inicio: datetime | None = None
    fecha_cierre: datetime | None = None


class ActividadDev(BaseModel):
    id_usuario: int
    nombre: str
    seniority: str
    tareas: list[TareaActividad]
    resumen: str | None = None
    resumen_fecha: datetime | None = None


class ResumenDev(BaseModel):
    resumen: str | None = None
    fecha: datetime | None = None
    sin_servicio: bool = False
