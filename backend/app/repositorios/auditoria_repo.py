from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.mongo import COL_LOGS, obtener_mongo

TTL_DIAS_DEFECTO = 90


async def registrar_evento(
    *,
    tipo_evento: str,
    contexto: dict[str, Any],
    id_usuario_postgres: int | None = None,
    id_tarea_postgres: int | None = None,
    ttl_dias: int = TTL_DIAS_DEFECTO,
) -> None:
    ahora = datetime.now(timezone.utc)
    await obtener_mongo()[COL_LOGS].insert_one(
        {
            "tipo_evento": tipo_evento,
            "fecha": ahora,
            "id_usuario_postgres": id_usuario_postgres,
            "id_tarea_postgres": id_tarea_postgres,
            "contexto": contexto,
            "ttl_expira": ahora + timedelta(days=ttl_dias),
        }
    )


async def listar_por_usuario(
    id_usuario_postgres: int, tipo_prefijo: str | None = None
) -> list[dict[str, Any]]:
    filtro: dict[str, Any] = {"id_usuario_postgres": id_usuario_postgres}
    if tipo_prefijo:
        filtro["tipo_evento"] = {"$regex": f"^{tipo_prefijo}"}
    cursor = obtener_mongo()[COL_LOGS].find(filtro, {"_id": 0}).sort("fecha", -1)
    return [doc async for doc in cursor]


async def contar_eventos_recientes(
    tipo_evento: str, id_usuario_postgres: int, desde: datetime
) -> int:
    return await obtener_mongo()[COL_LOGS].count_documents(
        {"tipo_evento": tipo_evento, "id_usuario_postgres": id_usuario_postgres, "fecha": {"$gte": desde}}
    )
