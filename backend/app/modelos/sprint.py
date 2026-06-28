"""Modelo Sprint."""
from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_datos import Base
from app.modelos.enums import EstadoSprint


class Sprint(Base):
    __tablename__ = "sprint"

    id_sprint: Mapped[int] = mapped_column(primary_key=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    objetivo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoSprint] = mapped_column(
        String(20), default=EstadoSprint.PLANIFICADO, nullable=False
    )

    tareas: Mapped[list["Tarea"]] = relationship(
        back_populates="sprint", cascade="all, delete-orphan"
    )
