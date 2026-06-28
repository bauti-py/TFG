"""Modelo TransicionEstado."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_datos import Base
from app.modelos.enums import EstadoTarea


class TransicionEstado(Base):
    __tablename__ = "transicion_estado"

    id_transicion: Mapped[int] = mapped_column(primary_key=True)
    estado: Mapped[EstadoTarea] = mapped_column(String(25), nullable=False)
    fecha_transicion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    id_tarea: Mapped[int] = mapped_column(
        ForeignKey("tarea.id_tarea", ondelete="CASCADE"), nullable=False
    )

    tarea: Mapped["Tarea"] = relationship(back_populates="transiciones")
