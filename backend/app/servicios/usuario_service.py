"""Servicio de usuarios / desarrolladores (CU2, RF18-20) y bootstrap de roles."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.seguridad import hashear_password, password_es_robusta
from app.esquemas.usuario import UsuarioActualizar, UsuarioCrear
from app.modelos.enums import RolNombre
from app.modelos.rol import Rol
from app.modelos.usuario import Usuario
from app.repositorios import perfil_repo


async def obtener_o_crear_rol(db: AsyncSession, nombre: RolNombre) -> Rol:
    rol = (await db.execute(select(Rol).where(Rol.nombre == nombre.value))).scalar_one_or_none()
    if rol is None:
        rol = Rol(nombre=nombre)
        db.add(rol)
        await db.flush()
    return rol


async def obtener_por_email(db: AsyncSession, email: str) -> Usuario | None:
    return (
        await db.execute(
            select(Usuario).options(selectinload(Usuario.rol)).where(Usuario.email == email)
        )
    ).scalar_one_or_none()


async def obtener_por_id(db: AsyncSession, id_usuario: int) -> Usuario | None:
    return (
        await db.execute(
            select(Usuario).options(selectinload(Usuario.rol)).where(Usuario.id_usuario == id_usuario)
        )
    ).scalar_one_or_none()


async def listar_por_rol(db: AsyncSession, rol: RolNombre, solo_activos: bool = True) -> list[Usuario]:
    consulta = select(Usuario).join(Rol).where(Rol.nombre == rol.value)
    if solo_activos:
        consulta = consulta.where(Usuario.activo.is_(True))
    return list((await db.execute(consulta)).scalars().all())


async def directorio(db: AsyncSession) -> dict[int, str]:
    """Mapa id_usuario → nombre para resolver nombres en el front (todos los roles)."""
    filas = (await db.execute(select(Usuario.id_usuario, Usuario.nombre))).all()
    return {fila[0]: fila[1] for fila in filas}


async def crear_usuario(db: AsyncSession, data: UsuarioCrear) -> Usuario:
    if not password_es_robusta(data.password):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La contraseña debe tener ≥8 caracteres, mayúscula, minúscula, dígito y carácter especial",
        )
    if await obtener_por_email(db, data.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un usuario con ese correo")

    rol = await obtener_o_crear_rol(db, data.rol)
    usuario = Usuario(
        nombre=data.nombre,
        email=data.email,
        contrasena_hash=hashear_password(data.password),
        id_rol=rol.id_rol,
    )
    db.add(usuario)
    await db.flush()

    await perfil_repo.crear_perfil(
        usuario.id_usuario,
        data.perfil.lenguajes,
        data.perfil.dominios,
        data.perfil.frameworks,
        data.perfil.seniority,
    )
    return usuario


async def actualizar_usuario(db: AsyncSession, id_usuario: int, data: UsuarioActualizar) -> Usuario:
    usuario = await obtener_por_id(db, id_usuario)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Desarrollador inexistente")

    if data.email and data.email != usuario.email:
        if await obtener_por_email(db, data.email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un usuario con ese correo")
        usuario.email = data.email
    if data.nombre:
        usuario.nombre = data.nombre
    if data.password:
        if not password_es_robusta(data.password):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La contraseña no cumple la política de robustez")
        usuario.contrasena_hash = hashear_password(data.password)
    if data.activo is not None:
        usuario.activo = data.activo
    if data.perfil is not None:
        await perfil_repo.actualizar_perfil(
            id_usuario,
            {
                "lenguajes": data.perfil.lenguajes,
                "dominios": data.perfil.dominios,
                "frameworks": data.perfil.frameworks,
                "seniority": data.perfil.seniority,
            },
        )
    await db.flush()
    return usuario


async def eliminar_desarrollador(db: AsyncSession, id_usuario: int) -> None:
    """Baja lógica: conserva el histórico (RF20) y libera las tareas activas (CU2)."""
    # Import local: evita el ciclo usuario_service -> estado_service -> ... -> usuario_service.
    from app.modelos.enums import EstadoTarea
    from app.modelos.tarea import Tarea
    from app.servicios import estado_service

    usuario = await obtener_por_id(db, id_usuario)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Desarrollador inexistente")
    usuario.activo = False

    # Sus tareas no terminadas se liberan para reasignación (CU2, alternativa).
    tareas = (
        await db.execute(select(Tarea).where(Tarea.id_usuario_asignado == id_usuario))
    ).scalars().all()
    activos = {EstadoTarea.ASIGNADA, EstadoTarea.EN_PROGRESO, EstadoTarea.BLOQUEADA}
    estados = await estado_service.estados_actuales(db, [t.id_tarea for t in tareas])
    for t in tareas:
        if estados.get(t.id_tarea) in activos:
            t.id_usuario_asignado = None
            await estado_service.cambiar_estado(db, t, EstadoTarea.PENDIENTE_ASIGNACION, validar=False)
    await db.flush()
