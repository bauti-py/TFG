"""Repositorio de perfiles de conocimiento (MongoDB, RF2/RF23)."""
from datetime import datetime, timezone
from typing import Any

from app.core.mongo import COL_PERFILES, obtener_mongo


async def crear_perfil(
    id_usuario: int,
    lenguajes: list[str],
    dominios: list[str],
    frameworks: list[str],
    seniority: str | None,
) -> None:
    ahora = datetime.now(timezone.utc)
    doc = {
        "id_usuario_postgres": id_usuario,
        "fecha_creacion": ahora,
        "fecha_ultima_actualizacion": ahora,
        "lenguajes": lenguajes,
        "dominios": dominios,
        "frameworks": frameworks,
        "seniority": seniority,
        "historial_tareas": {},
        "metricas_agregadas": {},
    }
    await obtener_mongo()[COL_PERFILES].update_one(
        {"id_usuario_postgres": id_usuario}, {"$set": doc}, upsert=True
    )


async def obtener_perfil(id_usuario: int) -> dict[str, Any] | None:
    return await obtener_mongo()[COL_PERFILES].find_one(
        {"id_usuario_postgres": id_usuario}, {"_id": 0}
    )


async def actualizar_perfil(id_usuario: int, campos: dict[str, Any]) -> None:
    campos = {**campos, "fecha_ultima_actualizacion": datetime.now(timezone.utc)}
    await obtener_mongo()[COL_PERFILES].update_one(
        {"id_usuario_postgres": id_usuario}, {"$set": campos}, upsert=True
    )


async def eliminar_perfil(id_usuario: int) -> None:
    await obtener_mongo()[COL_PERFILES].delete_one({"id_usuario_postgres": id_usuario})


async def incorporar_aprendizaje(id_usuario: int, lenguajes: list[str], dominios: list[str]) -> None:
    """Suma las tecnologías de una tarea completada e incrementa contadores (RF23, CU8)."""
    perfil = await obtener_perfil(id_usuario) or {}
    leng = set(perfil.get("lenguajes", []))
    dom = set(perfil.get("dominios", []))
    metricas = dict(perfil.get("metricas_agregadas", {}))
    for tecnologia in [*lenguajes, *dominios]:
        metricas[tecnologia] = metricas.get(tecnologia, 0) + 1
    leng.update(lenguajes)
    dom.update(dominios)
    await actualizar_perfil(
        id_usuario,
        {"lenguajes": sorted(leng), "dominios": sorted(dom), "metricas_agregadas": metricas},
    )
