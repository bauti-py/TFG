"""Servicio de tareas / backlog (CU1, RF1)."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.esquemas.tarea import ResultadoAsignacion, TareaCrear, TareaSalida
from app.modelos.enums import EstadoSprint
from app.modelos.sprint import Sprint
from app.modelos.tarea import Tarea
from app.servicios import asignacion_service, estado_service


def habilidades_lista(texto: str) -> list[str]:
    return [h.strip() for h in (texto or "").split(",") if h.strip()]


# Palabra clave en la descripción -> habilidad. Respaldo determinista para inferir las
# habilidades cuando el form no las manda (la IA igual puede afinarlas en la asignación).
_CLAVES_HABILIDAD: dict[str, str] = {
    "python": "python", "fastapi": "fastapi", "django": "django", "flask": "flask",
    "sql": "sql", "postgres": "sql", "mongodb": "mongodb", "mongo": "mongodb",
    "react": "react", "typescript": "typescript", "javascript": "javascript",
    "node": "node", "express": "express", "java": "java", "kotlin": "kotlin",
    "spring": "spring", "css": "css", "html": "html",
    "frontend": "frontend", "kanban": "frontend", "pantalla": "frontend",
    "dashboard": "frontend", "login": "frontend", "responsive": "ui",
    "formulario": "ui", "ui": "ui", "componentes": "frontend",
    "backend": "backend", "endpoint": "backend", "microservicio": "backend",
    "jwt": "backend", "autenticación": "backend", "autenticacion": "backend",
    "notificacion": "backend", "api": "apis", "rest": "apis", "openapi": "apis",
    "datos": "datos", "esquema": "datos", "modelar": "datos", "consultas": "datos",
    "métricas": "datos", "metricas": "datos",
}


def inferir_habilidades(descripcion: str) -> list[str]:
    texto = (descripcion or "").lower()
    inferidas: list[str] = []
    for clave, habilidad in _CLAVES_HABILIDAD.items():
        if clave in texto and habilidad not in inferidas:
            inferidas.append(habilidad)
    return inferidas


async def registrar_tarea(
    db: AsyncSession, id_sprint: int, data: TareaCrear
) -> tuple[Tarea, ResultadoAsignacion]:
    sprint = await db.get(Sprint, id_sprint)
    if sprint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El sprint indicado no existe")
    if sprint.estado == EstadoSprint.CERRADO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pueden registrar tareas en un sprint cerrado")

    habilidades = [
        h.strip().lower()
        for h in (data.habilidades_requeridas or inferir_habilidades(data.descripcion))
        if h.strip()
    ]
    tarea = Tarea(
        descripcion=data.descripcion,
        prioridad=data.prioridad,
        habilidades_requeridas=", ".join(habilidades),
        id_sprint=id_sprint,
    )
    db.add(tarea)
    await db.flush()
    await estado_service.registrar_estado_inicial(db, tarea)

    resultado = await asignacion_service.asignar_tarea(db, tarea)
    return tarea, resultado


async def obtener_tarea(db: AsyncSession, id_tarea: int) -> Tarea | None:
    return await db.get(Tarea, id_tarea)


async def descripciones(db: AsyncSession, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    filas = (
        await db.execute(select(Tarea.id_tarea, Tarea.descripcion).where(Tarea.id_tarea.in_(ids)))
    ).all()
    return {id_tarea: descripcion for id_tarea, descripcion in filas}


async def asignados(db: AsyncSession, ids: list[int]) -> dict[int, int | None]:
    """Mapa id_tarea -> id_usuario_asignado, para resolver el dev de cada bloqueo."""
    if not ids:
        return {}
    filas = (
        await db.execute(
            select(Tarea.id_tarea, Tarea.id_usuario_asignado).where(Tarea.id_tarea.in_(ids))
        )
    ).all()
    return {id_tarea: id_dev for id_tarea, id_dev in filas}


async def listar_por_sprint(db: AsyncSession, id_sprint: int) -> list[Tarea]:
    return list(
        (await db.execute(select(Tarea).where(Tarea.id_sprint == id_sprint))).scalars().all()
    )


async def listar_por_desarrollador(db: AsyncSession, id_usuario: int) -> list[Tarea]:
    return list(
        (await db.execute(select(Tarea).where(Tarea.id_usuario_asignado == id_usuario))).scalars().all()
    )


async def reasignar(db: AsyncSession, id_tarea: int) -> ResultadoAsignacion:
    tarea = await obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    return await asignacion_service.asignar_tarea(db, tarea)


async def asignar_manual(db: AsyncSession, id_tarea: int, id_usuario: int) -> ResultadoAsignacion:
    tarea = await obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    return await asignacion_service.asignar_manual(db, tarea, id_usuario)


async def eliminar(db: AsyncSession, id_tarea: int) -> None:
    tarea = await obtener_tarea(db, id_tarea)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    await db.delete(tarea)  # cascada: transiciones (ORM) y bloqueos (FK ondelete)
    await db.flush()


async def a_salida(db: AsyncSession, tarea: Tarea) -> TareaSalida:
    """Arma la representación de salida resolviendo el estado actual de la tarea."""
    estado = await estado_service.estado_actual(db, tarea.id_tarea)
    return TareaSalida(
        id_tarea=tarea.id_tarea,
        descripcion=tarea.descripcion,
        prioridad=tarea.prioridad,
        habilidades_requeridas=habilidades_lista(tarea.habilidades_requeridas),
        estado=estado,
        id_sprint=tarea.id_sprint,
        id_usuario_asignado=tarea.id_usuario_asignado,
        fecha_creacion=tarea.fecha_creacion,
        fecha_cierre=tarea.fecha_cierre,
    )
