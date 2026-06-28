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
