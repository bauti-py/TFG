# TaskFlow AI

**Plataforma de gestión de equipos de desarrollo potenciada por IA.**

TaskFlow AI automatiza la coordinación de un equipo de desarrollo de software mediante inteligencia artificial.

## ✨ Funcionalidades

* 🤖 **Asignación automática de tareas**: la IA infiere las habilidades requeridas a partir de la descripción de cada tarea y la asigna al desarrollador con mejor ajuste según su perfil y carga de trabajo.
* 💬 **Seguimiento conversacional**: un asistente reemplaza la reunión diaria, consulta el avance de cada desarrollador e infiere el estado de la tarea (En progreso, Bloqueada o Completada).
* 🚧 **Gestión de bloqueos**: los impedimentos se escalan automáticamente al Scrum Master y se notifican cuando se resuelven.
* 📊 **Dashboard de gestión**: tablero Kanban, backlog, sprints, métricas y seguimiento del equipo.

## 👥 Roles

* **Líder Técnico**: administra el backlog y el equipo.
* **Scrum Master**: gestiona sprints y bloqueos.
* **Desarrollador**: consulta y actualiza el estado de sus tareas.

---

# 🛠️ Stack tecnológico

| Capa                     | Tecnología                                |
| ------------------------ | ----------------------------------------- |
| Frontend                 | React + Vite + TypeScript                 |
| Backend                  | Python + FastAPI (Arquitectura por Capas) |
| Base de datos relacional | PostgreSQL                                |
| Base de datos documental | MongoDB                                   |
| IA                       | Google Gemini                             |
| Infraestructura          | Docker Compose                            |

---

# 📋 Requisitos

Solo necesitás instalar **Docker Desktop** (incluye Docker Compose).

No hace falta instalar:

* Node.js
* Python
* PostgreSQL
* MongoDB

Todo se ejecuta dentro de contenedores.

---

# 🚀 Puesta en marcha

## 1. Configurar variables de entorno

```bash
cp .env.example .env
```

## 2. Levantar todos los servicios

```bash
docker compose up -d --build
```

Se iniciarán automáticamente:

* Frontend
* Backend
* PostgreSQL
* MongoDB

---

## 🌐 Accesos

| Servicio   | URL                        |
| ---------- | -------------------------- |
| Aplicación | http://localhost:5173      |
| API        | http://localhost:8000      |
| Swagger    | http://localhost:8000/docs |

---

# 🔑 Usuario inicial

Durante el primer arranque el backend crea automáticamente:

* el esquema de PostgreSQL
* los índices de MongoDB
* un usuario **Líder Técnico** inicial

| Email                                   | Contraseña |
| --------------------------------------- | ---------- |
| [lider@demo.com](mailto:lider@demo.com) | Lider123!  |

---

# 🤖 Configuración de Gemini

La asignación automática utiliza la API de Google Gemini.

1. Obtener una API Key en:

https://aistudio.google.com/apikey

2. Agregarla al archivo `.env`

```env
GEMINI_API_KEY=tu_api_key
```

### ¿Qué ocurre si no configuro la API?

La aplicación funciona igualmente.

Simplemente las tareas quedarán con estado **"Asignación fallida"** y podrán asignarse manualmente desde el backlog mediante el botón 👤.

### Rotación automática de modelos

El cliente rota entre los modelos definidos en:

```env
GEMINI_MODELOS=
```

Cuando un modelo alcanza el límite de cuota (HTTP 429):

* queda temporalmente fuera de servicio
* se utiliza el siguiente modelo disponible
* si todos alcanzan su cuota, se utiliza un algoritmo determinista de respaldo.

---

# 🌱 Datos de demostración

El proyecto incluye un servicio **Seeder** que carga automáticamente datos de ejemplo cuando se ejecuta Docker Compose.

Se crean:

* 1 Scrum Master
* 5 Desarrolladores
* perfiles con distintas habilidades
* un Sprint activo
* un backlog de tareas

Si `GEMINI_API_KEY` está configurada, las tareas serán asignadas automáticamente por IA.

En caso contrario quedarán listas para asignación manual.

Las credenciales generadas se muestran en los logs del contenedor:

```bash
docker compose logs -f seeder
```

## Usuarios creados

El servicio **Seeder** crea automáticamente los siguientes usuarios de demostración:

| Rol           | Email            | Contraseña  |
| ------------- | ---------------- | ----------- |
| Líder Técnico | `lider@demo.com` | `Lider123!` |
| Scrum Master  | `sm@demo.com`    | `ScrumM1!`  |
| Desarrollador | `ana@demo.com`   | `Ana123!`   |
| Desarrollador | `bruno@demo.com` | `Bruno123!` |
| Desarrollador | `carla@demo.com` | `Carla123!` |
| Desarrollador | `diego@demo.com` | `Diego123!` |
| Desarrollador | `elena@demo.com` | `Elena123!` |

---

# 🐳 Servicios Docker

| Servicio   | Puerto |
| ---------- | ------ |
| Frontend   | 5173   |
| API        | 8000   |
| PostgreSQL | 5433   |
| MongoDB    | 27017  |

---

# 📦 Comandos útiles

Levantar el proyecto

```bash
docker compose up -d --build
```

Ver logs del backend

```bash
docker compose logs -f api
```

Ver logs del seeder

```bash
docker compose logs -f seeder
```

Detener los servicios

```bash
docker compose down
```

Eliminar también los volúmenes (reinicio completo)

```bash
docker compose down -v
```

---

# 📁 Estructura del proyecto

```text
backend/
└── app/
    ├── api/
    │   └── rutas/
    ├── servicios/
    ├── repositorios/
    ├── modelos/
    ├── esquemas/
    ├── ia/
    └── core/

frontend/
└── src/
    └── vistas/

scripts/
└── seed_demo.sh

docker-compose.yml
```

---

# 📝 Notas

* PostgreSQL se expone en el puerto **5433** para evitar conflictos con instalaciones locales.
* MongoDB utiliza el puerto **27017**.
* El frontend se sirve mediante **Nginx** y queda disponible en **http://localhost:5173**.
* El servicio **Seeder** espera automáticamente a que la API esté disponible antes de cargar los datos de demostración.
