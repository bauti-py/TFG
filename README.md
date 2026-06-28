# TaskFlow AI

**Plataforma de gestión de equipos de desarrollo potenciada por IA.**

TaskFlow AI automatiza la coordinación de un equipo de desarrollo de software:

- 🤖 **Asignación automática de tareas** — la IA infiere las habilidades que requiere cada tarea a partir de su descripción y la asigna al desarrollador con mejor ajuste según perfil y carga de trabajo.
- 💬 **Seguimiento conversacional** — un asistente reemplaza la reunión diaria: le pregunta al desarrollador cómo avanza e infiere el estado de la tarea (en progreso, bloqueada, completada).
- 🚧 **Gestión de bloqueos** — los impedimentos se escalan al Scrum Master y se notifican al desarrollador cuando se resuelven.
- 📊 **Tablero, backlog y sprints** — dashboard con kanban, métricas y avance por desarrollador.

Roles: **Líder Técnico** (backlog y equipo), **Scrum Master** (sprints y bloqueos) y **Desarrollador** (seguimiento de sus tareas).

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI (arquitectura por capas) |
| Datos | PostgreSQL (transaccional) + MongoDB (perfiles, conversaciones, auditoría) |
| IA | Google Gemini |
| Infra | Docker Compose |

## Requisitos

Solo necesitás **[Docker](https://www.docker.com/products/docker-desktop/)** (incluye Docker Compose). No hace falta instalar Node, Python, PostgreSQL ni MongoDB: todo corre en contenedores.

## Puesta en marcha

```bash
# 1. Configuración (una sola vez)
cp .env.example .env

# 2. Levantar todo (frontend + API + bases de datos)
docker compose up -d --build
```

Listo. Abrí la app en:

- 🖥️ **Aplicación: http://localhost:5173**
- 📚 API y documentación interactiva: http://localhost:8000/docs

Al arrancar, el backend crea el esquema, los índices y un **Líder Técnico inicial**:

| Email | Contraseña |
|-------|-----------|
| lider@demo.com | Lider123! |

> **IA (Gemini):** la asignación automática de tareas usa la API de Gemini. Conseguí una clave gratis en https://aistudio.google.com/apikey y pegala en `GEMINI_API_KEY` del `.env`. **Sin clave la app igual levanta y se puede usar, pero las tareas quedarán como «asignación fallida» y hay que asignarlas a mano** (con el botón 👤 en el backlog).
>
> El cliente rota entre varios modelos (`GEMINI_MODELOS` en `.env`): si uno agota su cuota (error 429), queda en pausa unos minutos (`GEMINI_TMP_OUT_MINUTOS`) y se usa el siguiente. Con el *free tier* la cuota diaria es baja; al agotarse todos, la app cae al *fallback* determinista.

### Datos de demo (opcional)

Carga 1 Scrum Master + 5 desarrolladores con perfiles distintos, crea un sprint activo con un backlog de tareas (que la IA asigna automáticamente si configuraste la `GEMINI_API_KEY`; sin clave quedan en «asignación fallida» para asignar a mano) e imprime las credenciales:

```bash
bash scripts/seed_demo.sh
```

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Líder Técnico | lider@demo.com | Lider123! |
| Scrum Master | sm@demo.com | ScrumM1! |
| Desarrolladores | ana@ / bruno@ / carla@ / diego@ / elena@demo.com | las imprime el seed |

## Comandos útiles

```bash
docker compose logs -f api      # ver logs del backend
docker compose up -d --build    # reconstruir tras cambios
docker compose down             # apagar
docker compose down -v          # apagar y borrar los datos (empezar de cero)
```

## Estructura

```
backend/app/
  api/rutas/     endpoints HTTP
  servicios/     lógica de negocio (casos de uso)
  repositorios/  acceso a MongoDB
  modelos/       SQLAlchemy (PostgreSQL)
  esquemas/      Pydantic (entrada/salida)
  ia/            cliente Gemini + TOON + prompts
  core/          config, seguridad (JWT/hash), conexiones
frontend/
  src/vistas/    pantallas (Login, Dashboard, Backlog, Sprints, …)
  Dockerfile     build con Vite, servido por nginx
docker-compose.yml · scripts/seed_demo.sh
```
