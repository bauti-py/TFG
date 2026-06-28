"""Modelo Bloqueo (impedimento detectado en el seguimiento, escalado al SM)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_datos import Base
from app.modelos.enums import EstadoBloqueo


class Bloqueo(Base):
    __tablename__ = "bloqueo"

    id_bloqueo: Mapped[int] = mapped_column(primary_key=True)
    contexto: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoBloqueo] = mapped_column(
        String(15), default=EstadoBloqueo.ABIERTO, nullable=False
    )
    resolucion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    id_tarea: Mapped[int] = mapped_column(ForeignKey("tarea.id_tarea", ondelete="CASCADE"), nullable=False)
    id_usuario_sm: Mapped[int | None] = mapped_column(ForeignKey("usuario.id_usuario"), nullable=True)
