"""Modelo Tarea."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_datos import Base
from app.modelos.enums import Prioridad


class Tarea(Base):
    __tablename__ = "tarea"

    id_tarea: Mapped[int] = mapped_column(primary_key=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    prioridad: Mapped[Prioridad] = mapped_column(String(15), default=Prioridad.MEDIA, nullable=False)
    habilidades_requeridas: Mapped[str] = mapped_column(Text, default="")
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    id_sprint: Mapped[int] = mapped_column(
        ForeignKey("sprint.id_sprint", ondelete="CASCADE"), nullable=False
    )
    id_usuario_asignado: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id_usuario"), nullable=True
    )

    sprint: Mapped["Sprint"] = relationship(back_populates="tareas")
    transiciones: Mapped[list["TransicionEstado"]] = relationship(
        back_populates="tarea", cascade="all, delete-orphan"
    )
