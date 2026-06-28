"""Enumeraciones del dominio."""
import enum


class RolNombre(str, enum.Enum):
    LIDER_TECNICO = "LIDER_TECNICO"
    DESARROLLADOR = "DESARROLLADOR"
    SCRUM_MASTER = "SCRUM_MASTER"


class Prioridad(str, enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class EstadoTarea(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PENDIENTE_ASIGNACION = "PENDIENTE_ASIGNACION"
    ASIGNADA = "ASIGNADA"
    EN_PROGRESO = "EN_PROGRESO"
    BLOQUEADA = "BLOQUEADA"
    COMPLETADA = "COMPLETADA"
    ASIGNACION_FALLIDA = "ASIGNACION_FALLIDA"


class EstadoSprint(str, enum.Enum):
    PLANIFICADO = "PLANIFICADO"
    ACTIVO = "ACTIVO"
    CERRADO = "CERRADO"


class EstadoBloqueo(str, enum.Enum):
    ABIERTO = "ABIERTO"
    RESUELTO = "RESUELTO"
    PERSISTENTE = "PERSISTENTE"
    ESCALADO_TL = "ESCALADO_TL"


def valor(e) -> str:
    """Valor textual de un enum, tolerando que ya venga como str (columnas String)."""
    return e.value if hasattr(e, "value") else str(e)
