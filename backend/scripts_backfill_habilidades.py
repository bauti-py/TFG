"""Backfill de una sola vez: completa habilidades vacías de tareas existentes y reaplica
el aprendizaje al perfil de los devs por sus tareas ya COMPLETADAS.

    docker compose exec -T api python - < backend/scripts_backfill_habilidades.py
"""
import asyncio

from sqlalchemy import select

from app.core.base_datos import SesionLocal
from app.modelos.enums import EstadoTarea
from app.modelos.tarea import Tarea
from app.servicios import estado_service, perfil_service
from app.servicios.tarea_service import habilidades_lista, inferir_habilidades


async def main() -> None:
    async with SesionLocal() as db:
        tareas = list((await db.execute(select(Tarea))).scalars().all())

        for t in tareas:
            if not (t.habilidades_requeridas or "").strip():
                t.habilidades_requeridas = ", ".join(inferir_habilidades(t.descripcion))
        await db.flush()

        estados = await estado_service.estados_actuales(db, [t.id_tarea for t in tareas])
        aplicadas = 0
        for t in tareas:
            if estados.get(t.id_tarea) == EstadoTarea.COMPLETADA and t.id_usuario_asignado:
                habs = habilidades_lista(t.habilidades_requeridas)
                if habs:
                    await perfil_service.actualizar_por_tarea_completada(t.id_usuario_asignado, habs)
                    aplicadas += 1
        await db.commit()
        print(f"backfill OK: {len(tareas)} tareas revisadas, aprendizaje aplicado a {aplicadas} completadas")


asyncio.run(main())
