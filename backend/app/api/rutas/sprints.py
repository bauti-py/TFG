"""Router de gestión de sprints (CU9, RF15-17). Atribución del Scrum Master."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import obtener_usuario_actual, requiere_rol
from app.esquemas.sprint import SprintActualizar, SprintCrear, SprintSalida
from app.modelos.enums import RolNombre
from app.servicios import sprint_service

router = APIRouter(prefix="/sprints", tags=["Sprints"])

_solo_sm = requiere_rol(RolNombre.SCRUM_MASTER)


@router.post("", response_model=SprintSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(_solo_sm)])
async def crear(data: SprintCrear, db: AsyncSession = Depends(obtener_db)):
    return await sprint_service.crear_sprint(db, data)


@router.get("", response_model=list[SprintSalida], dependencies=[Depends(obtener_usuario_actual)])
async def listar(db: AsyncSession = Depends(obtener_db)):
    return await sprint_service.listar_sprints(db)


@router.put("/{id_sprint}", response_model=SprintSalida, dependencies=[Depends(_solo_sm)])
async def actualizar(id_sprint: int, data: SprintActualizar, db: AsyncSession = Depends(obtener_db)):
    return await sprint_service.actualizar_sprint(db, id_sprint, data)


@router.delete("/{id_sprint}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(_solo_sm)])
async def eliminar(id_sprint: int, db: AsyncSession = Depends(obtener_db)):
    await sprint_service.eliminar_sprint(db, id_sprint)
