from datetime import datetime, timezone
from typing import Any
from app.core.mongo import COL_CONVERSACIONES, obtener_mongo


async def agregar_consulta(id_tarea: int, id_usuario: int | None, pregunta: str) -> None:
    await obtener_mongo()[COL_CONVERSACIONES].insert_one(
        {
            "id_tarea_postgres": id_tarea,
            "id_usuario_postgres": id_usuario,
            "fecha_consulta": datetime.now(timezone.utc),
            "fecha_respuesta": None,
            "consulta": {"texto": pregunta},
            "respuesta": None,
            "inferencia": None,
        }
    )


async def registrar_respuesta(
    id_tarea: int, texto: str, inferencia: dict | None, diferido: bool = False
) -> None:
    """Completa el ciclo abierto más reciente de la tarea con la respuesta del dev."""
    col = obtener_mongo()[COL_CONVERSACIONES]
    ciclo = await col.find_one(
        {"id_tarea_postgres": id_tarea, "respuesta": None}, sort=[("fecha_consulta", -1)]
    )
    valores = {
        "fecha_respuesta": datetime.now(timezone.utc),
        "respuesta": {"texto": texto, "pendiente_procesar": diferido},
        "inferencia": inferencia,
    }
    if ciclo is not None:
        await col.update_one({"_id": ciclo["_id"]}, {"$set": valores})
    else:
        await col.insert_one(
            {"id_tarea_postgres": id_tarea, "id_usuario_postgres": None, "fecha_consulta": None, **valores}
        )


async def listar_por_tarea(id_tarea: int) -> list[dict[str, Any]]:
    cursor = (
        obtener_mongo()[COL_CONVERSACIONES]
        .find({"id_tarea_postgres": id_tarea}, {"_id": 0})
        .sort("fecha_consulta", 1)
    )
    return [doc async for doc in cursor]


async def listar_diferidos() -> list[dict[str, Any]]:
    """Ciclos cuya respuesta quedó pendiente de procesar (IA caída, CU4 alternativo)."""
    cursor = obtener_mongo()[COL_CONVERSACIONES].find(
        {"respuesta.pendiente_procesar": True}, {"_id": 0}
    )
    return [doc async for doc in cursor]
