"""Capa de persistencia documental (MongoDB vía Motor)."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import config

COL_PERFILES = "perfiles_conocimiento"
COL_CONVERSACIONES = "conversaciones"
COL_LOGS = "logs_auditoria"

_cliente: AsyncIOMotorClient | None = None


def obtener_cliente() -> AsyncIOMotorClient:
    global _cliente
    if _cliente is None:
        _cliente = AsyncIOMotorClient(config.MONGO_URI)
    return _cliente


def obtener_mongo() -> AsyncIOMotorDatabase:
    return obtener_cliente()[config.MONGO_DB]


async def crear_indices() -> None:
    """Crea los índices base de las tres colecciones."""
    db = obtener_mongo()
    await db[COL_PERFILES].create_index("id_usuario_postgres", unique=True)
    await db[COL_CONVERSACIONES].create_index("id_tarea_postgres")
    await db[COL_LOGS].create_index("fecha")
    await db[COL_LOGS].create_index("id_usuario_postgres")
    await db[COL_LOGS].create_index("tipo_evento")
    await db[COL_LOGS].create_index("ttl_expira", expireAfterSeconds=0)


async def cerrar_mongo() -> None:
    global _cliente
    if _cliente is not None:
        _cliente.close()
        _cliente = None
