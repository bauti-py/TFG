from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.modelos  # noqa: F401  — registra los modelos ORM en Base.metadata para crear_esquema()
from app.api.rutas import auth, bloqueos, dashboard, seguimiento, sprints, tareas, usuarios
from app.core.base_datos import SesionLocal, crear_esquema
from app.core.config import config
from app.core.mongo import cerrar_mongo, crear_indices
from app.esquemas.usuario import PerfilEntrada, UsuarioCrear
from app.modelos.enums import RolNombre
from app.servicios.usuario_service import crear_usuario, listar_por_rol, obtener_o_crear_rol


async def _bootstrap(db) -> None:
    for rol in RolNombre:
        await obtener_o_crear_rol(db, rol)
    if not await listar_por_rol(db, RolNombre.LIDER_TECNICO, solo_activos=False):
        await crear_usuario(
            db,
            UsuarioCrear(
                nombre=config.BOOTSTRAP_ADMIN_NOMBRE,
                email=config.BOOTSTRAP_ADMIN_EMAIL,
                password=config.BOOTSTRAP_ADMIN_PASSWORD,
                rol=RolNombre.LIDER_TECNICO,
                perfil=PerfilEntrada(),
            ),
        )


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    await crear_esquema()
    await crear_indices()
    async with SesionLocal() as db:
        await _bootstrap(db)
        await db.commit()
    yield
    await cerrar_mongo()


app = FastAPI(
    title=config.APP_NOMBRE,
    description="Backend de la Plataforma de Gestión de Equipos de Desarrollo Inteligente.",
    version="0.1.0",
    lifespan=ciclo_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for enrutador in (
    auth.router,
    usuarios.router,
    sprints.router,
    tareas.router,
    tareas.tareas_router,
    seguimiento.router,
    bloqueos.router,
    dashboard.router,
):
    app.include_router(enrutador, prefix=config.API_PREFIJO)


@app.get("/health", tags=["Infra"])
async def health():
    return {"status": "ok", "app": config.APP_NOMBRE}
