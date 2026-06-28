"""Dashboard del sprint, personalizado por rol (CU7, RF14)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modelos.enums import EstadoTarea, RolNombre, valor
from app.modelos.tarea import Tarea
from app.servicios import bloqueo_service, estado_service
from app.servicios.sprint_service import obtener_sprint_activo
from app.servicios.tarea_service import listar_por_desarrollador


async def _columnas(db: AsyncSession, tareas: list[Tarea]) -> dict[str, list[dict]]:
    columnas: dict[str, list[dict]] = {e.value: [] for e in EstadoTarea}
    estados = await estado_service.estados_actuales(db, [t.id_tarea for t in tareas])
    for t in tareas:
        estado = estados.get(t.id_tarea, EstadoTarea.PENDIENTE)
        columnas[estado.value].append(
            {
                "id_tarea": t.id_tarea,
                "descripcion": t.descripcion,
                "prioridad": valor(t.prioridad),
                "id_usuario_asignado": t.id_usuario_asignado,
                "fecha_creacion": t.fecha_creacion.isoformat() if t.fecha_creacion else None,
            }
        )
    return columnas


async def dashboard_desarrollador(db: AsyncSession, id_usuario: int) -> dict:
    """Vista del desarrollador: solo sus tareas asignadas (RF14)."""
    tareas = await listar_por_desarrollador(db, id_usuario)
    return {
        "rol": RolNombre.DESARROLLADOR.value,
        "total_tareas": len(tareas),
        "columnas": await _columnas(db, tareas),
    }


async def dashboard_global(db: AsyncSession) -> dict:
    """Vista global del Scrum Master / Líder Técnico: todo el sprint activo (RF14)."""
    sprint = await obtener_sprint_activo(db)
    if sprint is None:
        return {"sprint": None, "mensaje": "No hay sprint activo"}

    tareas = list(
        (await db.execute(select(Tarea).where(Tarea.id_sprint == sprint.id_sprint))).scalars().all()
    )
    estados = await estado_service.estados_actuales(db, [t.id_tarea for t in tareas])

    activos = {EstadoTarea.ASIGNADA, EstadoTarea.EN_PROGRESO, EstadoTarea.BLOQUEADA}
    por_dev: dict[int, int] = {}
    for t in tareas:
        if t.id_usuario_asignado and estados.get(t.id_tarea) in activos:
            por_dev[t.id_usuario_asignado] = por_dev.get(t.id_usuario_asignado, 0) + 1

    completadas = sum(1 for t in tareas if estados.get(t.id_tarea) == EstadoTarea.COMPLETADA)
    descripciones = {t.id_tarea: t.descripcion for t in tareas}
    bloqueos = await bloqueo_service.listar_abiertos(db)
    return {
        "sprint": {"id_sprint": sprint.id_sprint, "objetivo": sprint.objetivo, "estado": valor(sprint.estado)},
        "total_tareas": len(tareas),
        "completadas": completadas,
        "progreso": round(completadas / len(tareas), 2) if tareas else 0.0,
        "columnas": await _columnas(db, tareas),
        "tareas_activas_por_desarrollador": por_dev,
        "bloqueos_pendientes": [
            {
                "id_bloqueo": b.id_bloqueo, "id_tarea": b.id_tarea,
                "descripcion": descripciones.get(b.id_tarea), "contexto": b.contexto,
            }
            for b in bloqueos
        ],
    }
