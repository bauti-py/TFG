"""Router de gestión de Desarrolladores/usuarios (CU2, RF18-20)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_datos import obtener_db
from app.core.dependencias import obtener_usuario_actual, requiere_rol
from app.esquemas.usuario import PerfilSalida, UsuarioActualizar, UsuarioCrear, UsuarioSalida
from app.modelos.enums import RolNombre
from app.repositorios import perfil_repo
from app.servicios import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios / Desarrolladores"])

_solo_tl = requiere_rol(RolNombre.LIDER_TECNICO)


@router.get("/directorio", dependencies=[Depends(obtener_usuario_actual)])
async def directorio(db: AsyncSession = Depends(obtener_db)) -> dict[int, str]:
    """Mapa id→nombre de todos los usuarios (para mostrar nombres en lugar de #id)."""
    return await usuario_service.directorio(db)


@router.post("", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(_solo_tl)])
async def crear(data: UsuarioCrear, db: AsyncSession = Depends(obtener_db)):
    usuario = await usuario_service.crear_usuario(db, data)
    return UsuarioSalida(
        id_usuario=usuario.id_usuario, nombre=usuario.nombre, email=usuario.email,
        rol=data.rol, activo=usuario.activo,
    )


@router.get("", response_model=list[UsuarioSalida], dependencies=[Depends(_solo_tl)])
async def listar(db: AsyncSession = Depends(obtener_db)):
    devs = await usuario_service.listar_por_rol(db, RolNombre.DESARROLLADOR, solo_activos=False)
    return [
        UsuarioSalida(
            id_usuario=d.id_usuario, nombre=d.nombre, email=d.email,
            rol=RolNombre.DESARROLLADOR, activo=d.activo,
        )
        for d in devs
    ]


@router.get("/{id_usuario}/perfil", response_model=PerfilSalida, dependencies=[Depends(_solo_tl)])
async def ver_perfil(id_usuario: int):
    perfil = await perfil_repo.obtener_perfil(id_usuario)
    if perfil is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perfil inexistente")
    return PerfilSalida(**perfil)


@router.put("/{id_usuario}", response_model=UsuarioSalida, dependencies=[Depends(_solo_tl)])
async def actualizar(id_usuario: int, data: UsuarioActualizar, db: AsyncSession = Depends(obtener_db)):
    usuario = await usuario_service.actualizar_usuario(db, id_usuario, data)
    return UsuarioSalida(
        id_usuario=usuario.id_usuario, nombre=usuario.nombre, email=usuario.email,
        rol=usuario.rol.nombre, activo=usuario.activo,
    )


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(_solo_tl)])
async def eliminar(id_usuario: int, db: AsyncSession = Depends(obtener_db)):
    await usuario_service.eliminar_desarrollador(db, id_usuario)
