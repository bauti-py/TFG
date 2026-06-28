"""Seguimiento del equipo para el Scrum Master: tracking por desarrollador + resumen IA."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mongo import COL_RESUMENES_DEV, obtener_mongo
from app.ia import cliente_gemini, prompts
from app.modelos.enums import EstadoTarea, RolNombre
from app.modelos.tarea import Tarea
from app.modelos.transicion_estado import TransicionEstado
from app.repositorios import conversacion_repo, perfil_repo
from app.servicios import estado_service, sprint_service, tarea_service, usuario_service


_ESTADOS_ARRANQUE = [
    EstadoTarea.EN_PROGRESO.value, EstadoTarea.BLOQUEADA.value, EstadoTarea.COMPLETADA.value,
]


async def _inicios_por_tarea(db: AsyncSession, ids_tarea: list[int]) -> dict[int, datetime]:
    """Cuándo se 'arrancó' cada tarea: primera vez que salió de ASIGNADA a un estado de
    trabajo (EN_PROGRESO, BLOQUEADA o COMPLETADA). Una tarea bloqueada sí fue arrancada."""
    if not ids_tarea:
        return {}
    filas = (
        await db.execute(
            select(TransicionEstado.id_tarea, TransicionEstado.fecha_transicion)
            .where(
                TransicionEstado.id_tarea.in_(ids_tarea),
                TransicionEstado.estado.in_(_ESTADOS_ARRANQUE),
            )
            .order_by(TransicionEstado.fecha_transicion.asc())
        )
    ).all()
    inicios: dict[int, datetime] = {}
    for id_tarea, fecha in filas:
        inicios.setdefault(id_tarea, fecha)  # la primera (orden asc) es el inicio real
    return inicios


async def _resumenes_cacheados(ids_dev: list[int]) -> dict[int, dict]:
    cursor = obtener_mongo()[COL_RESUMENES_DEV].find(
        {"id_usuario_postgres": {"$in": ids_dev}}, {"_id": 0}
    )
    return {d["id_usuario_postgres"]: d async for d in cursor}


async def actividad_equipo(db: AsyncSession) -> list[dict]:
    """Tracking estructurado (sin IA) de cada dev en el sprint activo + último resumen cacheado."""
    sprint = await sprint_service.obtener_sprint_activo(db)
    if sprint is None:
        return []

    tareas = await tarea_service.listar_por_sprint(db, sprint.id_sprint)
    estados = await estado_service.estados_actuales(db, [t.id_tarea for t in tareas])
    inicios = await _inicios_por_tarea(db, [t.id_tarea for t in tareas])
    devs = await usuario_service.listar_por_rol(db, RolNombre.DESARROLLADOR, solo_activos=True)
    cache = await _resumenes_cacheados([d.id_usuario for d in devs])

    por_dev: dict[int, list[Tarea]] = {}
    for t in tareas:
        if t.id_usuario_asignado is not None:
            por_dev.setdefault(t.id_usuario_asignado, []).append(t)

    salida = []
    for dev in devs:
        perfil = await perfil_repo.obtener_perfil(dev.id_usuario) or {}
        sus_tareas = por_dev.get(dev.id_usuario, [])
        resumen = cache.get(dev.id_usuario)
        salida.append(
            {
                "id_usuario": dev.id_usuario,
                "nombre": dev.nombre,
                "seniority": perfil.get("seniority", "N/D"),
                "tareas": [
                    {
                        "id_tarea": t.id_tarea,
                        "descripcion": t.descripcion,
                        "estado": estados.get(t.id_tarea, EstadoTarea.PENDIENTE).value,
                        "fecha_inicio": inicios.get(t.id_tarea),
                        "fecha_cierre": t.fecha_cierre,
                    }
                    for t in sus_tareas
                ],
                "resumen": (resumen or {}).get("resumen"),
                "resumen_fecha": (resumen or {}).get("fecha"),
            }
        )
    return salida


async def generar_resumen_dev(db: AsyncSession, id_dev: int) -> dict:
    """Pide a la IA el resumen narrativo del avance del dev y lo cachea."""
    sprint = await sprint_service.obtener_sprint_activo(db)
    tareas = (
        [t for t in await tarea_service.listar_por_sprint(db, sprint.id_sprint) if t.id_usuario_asignado == id_dev]
        if sprint
        else []
    )
    dev = await usuario_service.obtener_por_id(db, id_dev)
    perfil = await perfil_repo.obtener_perfil(id_dev) or {}

    if not tareas:
        return {"resumen": "Este desarrollador no tiene tareas asignadas en el sprint activo.", "fecha": None}

    estados = await estado_service.estados_actuales(db, [t.id_tarea for t in tareas])
    inicios = await _inicios_por_tarea(db, [t.id_tarea for t in tareas])
    tareas_payload = [
        {
            "descripcion": t.descripcion,
            "estado": estados.get(t.id_tarea, EstadoTarea.PENDIENTE).value,
            "fecha_inicio": inicios.get(t.id_tarea).isoformat() if inicios.get(t.id_tarea) else None,
            "fecha_cierre": t.fecha_cierre.isoformat() if t.fecha_cierre else None,
            "conversacion": [
                {"pregunta": c["consulta"]["texto"], "respuesta": (c.get("respuesta") or {}).get("texto")}
                for c in await conversacion_repo.listar_por_tarea(t.id_tarea)
                if c.get("consulta")
            ],
        }
        for t in tareas
    ]
    dev_payload = {"nombre": dev.nombre if dev else "", "seniority": perfil.get("seniority", "N/D")}

    prompt, json_equivalente = prompts.prompt_resumen_actividad_dev(dev_payload, tareas_payload)
    resumen = await cliente_gemini.generar(
        tipo="resumen_actividad", prompt=prompt, id_usuario=id_dev,
        tokens_json_equivalente=json_equivalente,
    )
    if resumen is None:
        # Sin IA: no inventamos narrativa. El tracking estructurado igual se ve en la tabla.
        return {"resumen": None, "fecha": None, "sin_servicio": True}

    resumen = resumen.strip()
    fecha = datetime.now(timezone.utc)
    await obtener_mongo()[COL_RESUMENES_DEV].update_one(
        {"id_usuario_postgres": id_dev},
        {"$set": {"id_usuario_postgres": id_dev, "resumen": resumen, "fecha": fecha}},
        upsert=True,
    )
    return {"resumen": resumen, "fecha": fecha}
