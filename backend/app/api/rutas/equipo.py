"""Seguimiento del equipo (Scrum Master / Líder Técnico): tracking + resumen IA por dev."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import requiere_rol
from app.esquemas.seguimiento import ActividadDev, ResumenDev
from app.modelos.enums import RolNombre
from app.servicios import equipo_service

router = APIRouter(prefix="/equipo", tags=["Seguimiento del equipo"])

_gestor = requiere_rol(RolNombre.SCRUM_MASTER, RolNombre.LIDER_TECNICO)


@router.get("/actividad", response_model=list[ActividadDev], dependencies=[Depends(_gestor)])
async def actividad(db: AsyncSession = Depends(obtener_db)):
    return await equipo_service.actividad_equipo(db)


@router.post("/{id_dev}/resumen", response_model=ResumenDev, dependencies=[Depends(_gestor)])
async def resumen_dev(id_dev: int, db: AsyncSession = Depends(obtener_db)):
    return await equipo_service.generar_resumen_dev(db, id_dev)
