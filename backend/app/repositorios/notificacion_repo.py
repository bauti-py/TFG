"""Notificaciones a usuarios (RF5, RF9, RF13)."""
from typing import Any

from app.repositorios import auditoria_repo


async def crear_notificacion(
    id_usuario: int, tipo: str, mensaje: str, data: dict | None = None
) -> None:
    await auditoria_repo.registrar_evento(
        tipo_evento=f"notificacion:{tipo}",
        contexto={"mensaje": mensaje, "data": data or {}, "leida": False},
        id_usuario_postgres=id_usuario,
        id_tarea_postgres=(data or {}).get("id_tarea"),
    )


async def listar_por_usuario(id_usuario: int, solo_no_leidas: bool = False) -> list[dict[str, Any]]:
    eventos = await auditoria_repo.listar_por_usuario(id_usuario, tipo_prefijo="notificacion:")
    notifs = [
        {
            "tipo": ev["tipo_evento"].removeprefix("notificacion:"),
            "mensaje": ev["contexto"].get("mensaje"),
            "data": ev["contexto"].get("data", {}),
            "leida": ev["contexto"].get("leida", False),
            "fecha": ev["fecha"],
        }
        for ev in eventos
    ]
    if solo_no_leidas:
        notifs = [n for n in notifs if not n["leida"]]
    return notifs
