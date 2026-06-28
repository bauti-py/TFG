"""Capa de persistencia relacional (PostgreSQL vía SQLAlchemy async)."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import config

motor = create_async_engine(config.postgres_dsn, echo=False, pool_pre_ping=True)

SesionLocal = async_sessionmaker(
    bind=motor, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""


async def obtener_db() -> AsyncGenerator[AsyncSession, None]:
    async with SesionLocal() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise


async def crear_esquema() -> None:
    """Crea las tablas declaradas si no existen (prototipo; en prod, migraciones).

    Los modelos los importa main.py al arrancar (registra Base.metadata); por eso acá
    no se importan: hacerlo arriba daría import circular (los modelos importan Base).
    """
    async with motor.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)
